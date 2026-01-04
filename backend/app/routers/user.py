"""
User Stats Router - Dashboard data endpoints (progress, streaks, activity)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.mongo import mongodb
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["User Stats"]
)


# ==================== SCHEMAS ====================

class DailyActivity(BaseModel):
    """Daily activity entry."""
    day: str = Field(..., description="Day name (Mon, Tue, etc.)")
    active: bool = Field(..., description="Whether user was active")
    hours: float = Field(..., description="Hours of activity")
    date: str = Field(..., description="Date string (YYYY-MM-DD)")


class StreakData(BaseModel):
    """User streak information."""
    current_streak: int = Field(..., description="Current consecutive days")
    longest_streak: int = Field(..., description="Longest streak ever")
    weekly_activity: List[DailyActivity] = Field(..., description="Last 7 days activity")
    last_activity_date: Optional[str] = Field(None, description="Last activity date")


class ProgressData(BaseModel):
    """User progress information."""
    overall_progress: int = Field(..., description="Overall progress percentage")
    total_tests: int = Field(..., description="Total tests available")
    completed_tests: int = Field(..., description="Tests completed")
    total_chapters: int = Field(..., description="Total chapters")
    completed_chapters: int = Field(..., description="Chapters completed")
    average_score: float = Field(..., description="Average test score")


class NoteSummary(BaseModel):
    """Note summary for dashboard."""
    id: str
    title: str
    lesson: str
    date: str
    subject: str


class DashboardData(BaseModel):
    """Complete dashboard data."""
    streak: StreakData
    progress: ProgressData
    recent_notes: List[NoteSummary]
    total_notes: int


# ==================== ENDPOINTS ====================

@router.get("/streak/{student_id}", response_model=StreakData)
async def get_streak_data(student_id: str):
    """
    Get user's activity streak and weekly activity.
    
    Calculates streak based on daily login/activity records in MongoDB.
    """
    try:
        logger.info(f"📊 Fetching streak data for student: {student_id}")
        
        # Get activity collection
        activities_col = mongodb.db["user_activities"]
        
        # Fetch last 30 days of activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        activities = await activities_col.find({
            "student_id": student_id,
            "date": {"$gte": thirty_days_ago.strftime("%Y-%m-%d")}
        }).sort("date", -1).to_list(length=30)
        
        # Calculate current streak
        current_streak = 0
        today = datetime.utcnow().date()
        check_date = today
        
        # Build set of active dates
        active_dates = {a["date"] for a in activities}
        
        while check_date.strftime("%Y-%m-%d") in active_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # Get longest streak from user profile or calculate
        user_col = mongodb.db["users"]
        user = await user_col.find_one({"student_id": student_id})
        longest_streak = user.get("longest_streak", current_streak) if user else current_streak
        
        # Update longest streak if current is higher
        if current_streak > longest_streak:
            longest_streak = current_streak
            await user_col.update_one(
                {"student_id": student_id},
                {"$set": {"longest_streak": longest_streak}},
                upsert=True
            )
        
        # Build weekly activity (last 7 days)
        weekly_activity = []
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        for i in range(6, -1, -1):  # Last 7 days
            day_date = today - timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            day_name = day_names[day_date.weekday()]
            
            # Find activity for this day
            day_activity = next((a for a in activities if a["date"] == day_str), None)
            
            weekly_activity.append(DailyActivity(
                day=day_name,
                active=day_activity is not None,
                hours=day_activity.get("hours", 0) if day_activity else 0,
                date=day_str
            ))
        
        last_activity = activities[0]["date"] if activities else None
        
        return StreakData(
            current_streak=current_streak,
            longest_streak=longest_streak,
            weekly_activity=weekly_activity,
            last_activity_date=last_activity
        )
        
    except Exception as e:
        logger.error(f"❌ Get streak error: {e}")
        # Return default data on error
        today = datetime.utcnow().date()
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly = []
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)
            weekly.append(DailyActivity(
                day=day_names[day_date.weekday()],
                active=False,
                hours=0,
                date=day_date.strftime("%Y-%m-%d")
            ))
        
        return StreakData(
            current_streak=0,
            longest_streak=0,
            weekly_activity=weekly,
            last_activity_date=None
        )


@router.get("/progress/{student_id}", response_model=ProgressData)
async def get_progress_data(
    student_id: str,
    subject: Optional[str] = Query(None, description="Filter by subject")
):
    """
    Get user's learning progress.
    
    Calculates progress from completed tests and chapters.
    """
    try:
        logger.info(f"📊 Fetching progress data for student: {student_id}")
        
        # Get evaluations collection
        eval_col = mongodb.db["evaluations"]
        
        # Build filter
        filter_query = {"student_id": student_id}
        if subject:
            filter_query["subject"] = subject
        
        # Fetch evaluations
        evaluations = await eval_col.find(filter_query).to_list(length=100)
        
        # Calculate stats
        completed_tests = len(evaluations)
        total_tests = 10  # Default total (can be made dynamic)
        
        # Calculate average score
        if evaluations:
            scores = [e.get("result", {}).get("percentage", 0) for e in evaluations]
            average_score = sum(scores) / len(scores)
        else:
            average_score = 0
        
        # Get completed chapters from notes/activities
        notes_col = mongodb.db["notes"]
        notes_filter = {"student_id": student_id}
        if subject:
            notes_filter["subject"] = subject
        
        notes = await notes_col.find(notes_filter).to_list(length=500)
        completed_chapters = len(set(n.get("chapter", 0) for n in notes if n.get("chapter")))
        
        total_chapters = 14  # Default total chapters
        
        # Calculate overall progress
        test_progress = (completed_tests / total_tests) * 50 if total_tests > 0 else 0
        chapter_progress = (completed_chapters / total_chapters) * 50 if total_chapters > 0 else 0
        overall_progress = int(test_progress + chapter_progress)
        
        return ProgressData(
            overall_progress=min(overall_progress, 100),
            total_tests=total_tests,
            completed_tests=completed_tests,
            total_chapters=total_chapters,
            completed_chapters=completed_chapters,
            average_score=round(average_score, 1)
        )
        
    except Exception as e:
        logger.error(f"❌ Get progress error: {e}")
        return ProgressData(
            overall_progress=0,
            total_tests=10,
            completed_tests=0,
            total_chapters=14,
            completed_chapters=0,
            average_score=0
        )


@router.get("/dashboard/{student_id}", response_model=DashboardData)
async def get_dashboard_data(
    student_id: str,
    subject: Optional[str] = Query(None, description="Filter by subject")
):
    """
    Get all dashboard data in one call.
    
    Returns streak, progress, and recent notes for efficiency.
    """
    try:
        logger.info(f"📊 Fetching dashboard data for student: {student_id}")
        
        # Get streak and progress
        streak = await get_streak_data(student_id)
        progress = await get_progress_data(student_id, subject)
        
        # Get recent notes
        notes_col = mongodb.db["notes"]
        notes_filter = {"student_id": student_id}
        if subject:
            notes_filter["subject"] = subject
        
        raw_notes = await notes_col.find(notes_filter).sort("created_at", -1).limit(5).to_list(length=5)
        
        recent_notes = []
        for note in raw_notes:
            created_at = note.get("created_at", datetime.utcnow())
            if isinstance(created_at, datetime):
                date_str = created_at.strftime("%b %d")
            else:
                date_str = str(created_at)[:10]
            
            recent_notes.append(NoteSummary(
                id=str(note.get("_id", "")),
                title=note.get("heading", note.get("note_content", "Untitled")[:30]),
                lesson=f"{note.get('subject', 'Unknown')} Ch {note.get('chapter', '?')}",
                date=date_str,
                subject=note.get("subject", "Unknown")
            ))
        
        # Get total notes count
        total_notes = await notes_col.count_documents(notes_filter)
        
        return DashboardData(
            streak=streak,
            progress=progress,
            recent_notes=recent_notes,
            total_notes=total_notes
        )
        
    except Exception as e:
        logger.error(f"❌ Get dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activity/log")
async def log_activity(
    student_id: str,
    hours: float = 0.5
):
    """
    Log user activity for streak tracking.
    
    Call this when user performs any action (opens PDF, uses chatbot, etc.)
    """
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        activities_col = mongodb.db["user_activities"]
        
        # Upsert today's activity
        result = await activities_col.update_one(
            {"student_id": student_id, "date": today},
            {
                "$inc": {"hours": hours},
                "$set": {"last_updated": datetime.utcnow()}
            },
            upsert=True
        )
        
        logger.info(f"✅ Logged activity for {student_id}: +{hours}h on {today}")
        
        return {"message": "Activity logged", "date": today, "hours_added": hours}
        
    except Exception as e:
        logger.error(f"❌ Log activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
