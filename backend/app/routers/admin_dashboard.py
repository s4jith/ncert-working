"""
Admin Dashboard Router
- Analytics and metrics
- Student management (CRUD)
- User statistics
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import hashlib
import logging

from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


# ==================== PYDANTIC MODELS ====================

class StudentCreate(BaseModel):
    """Model for creating a new student."""
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=5, le=25)
    class_level: int = Field(..., ge=5, le=12)
    email: str = Field(..., description="Gmail address")
    mobile: str = Field(..., min_length=10, max_length=15)


class StudentUpdate(BaseModel):
    """Model for updating a student."""
    name: Optional[str] = None
    age: Optional[int] = None
    class_level: Optional[int] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(BaseModel):
    """Model for student response."""
    id: str
    user_id: str
    name: str
    age: int
    email: str
    mobile: str
    class_level: int
    is_active: bool
    is_onboarded: bool
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    tests_completed: int = 0
    avg_score: float = 0.0


# ==================== HELPER FUNCTIONS ====================

def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_student_id(name: str, age: int) -> str:
    """
    Generate unique student ID.
    Format: {name_lowercase}{age}{sequential_number}
    Example: sajith141 (Sajith, age 14, student #1)
    """
    try:
        # Get next student number
        counter = db.student_counters.find_one_and_update(
            {"_id": "student_count"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True
        )
        student_number = counter.get("count", 1)
        
        # Generate ID: name (lowercase, no spaces) + age + number
        clean_name = name.lower().replace(" ", "").replace(".", "")[:10]
        user_id = f"{clean_name}{age}{student_number}"
        
        return user_id
    except Exception as e:
        logger.error(f"Error generating student ID: {e}")
        # Fallback: use timestamp
        import time
        clean_name = name.lower().replace(" ", "")[:10]
        return f"{clean_name}{age}{int(time.time()) % 10000}"


def generate_password(name: str, age: int) -> str:
    """
    Generate default password.
    Format: {name_lowercase}{age}
    Example: sajith14
    """
    clean_name = name.lower().replace(" ", "").replace(".", "")
    return f"{clean_name}{age}"


def serialize_student(student: dict) -> dict:
    """Convert MongoDB document to response dict."""
    return {
        "id": str(student.get("_id", "")),
        "user_id": student.get("user_id", ""),
        "name": student.get("name", ""),
        "age": student.get("age", 0),
        "email": student.get("email", ""),
        "mobile": student.get("mobile", ""),
        "class_level": student.get("class_level", 10),
        "is_active": student.get("is_active", True),
        "is_onboarded": student.get("isOnboarded", False),
        "created_at": student.get("created_at", datetime.utcnow()).isoformat() if student.get("created_at") else None,
        "last_login": student.get("last_login").isoformat() if student.get("last_login") else None,
        "tests_completed": student.get("tests_completed", 0),
        "avg_score": student.get("avg_score", 0.0)
    }


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics")
async def get_analytics():
    """
    Get comprehensive analytics for admin dashboard.
    Returns user stats, test stats, activity trends, etc.
    """
    try:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today_start - timedelta(days=7)
        month_ago = today_start - timedelta(days=30)
        
        # User Statistics
        total_users = db.users.count_documents({})
        total_students = db.users.count_documents({"role": "student"})
        total_teachers = db.users.count_documents({"role": "teacher"})
        
        # Active users (logged in today/week/month)
        active_today = db.users.count_documents({"last_login": {"$gte": today_start}})
        active_this_week = db.users.count_documents({"last_login": {"$gte": week_ago}})
        active_this_month = db.users.count_documents({"last_login": {"$gte": month_ago}})
        
        # Inactive users (no login in 30 days)
        inactive_users = db.users.count_documents({
            "$or": [
                {"last_login": {"$lt": month_ago}},
                {"last_login": None}
            ]
        })
        
        # New users
        new_users_today = db.users.count_documents({"created_at": {"$gte": today_start}})
        new_users_this_week = db.users.count_documents({"created_at": {"$gte": week_ago}})
        new_users_this_month = db.users.count_documents({"created_at": {"$gte": month_ago}})
        
        user_stats = {
            "total_users": total_users,
            "total_students": total_students,
            "total_teachers": total_teachers,
            "active_today": active_today,
            "active_this_week": active_this_week,
            "active_this_month": active_this_month,
            "inactive_users": inactive_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "new_users_this_month": new_users_this_month
        }
        
        # Test Statistics
        quiz_results = db.get_collection("quiz_results")
        total_tests_taken = quiz_results.count_documents({})
        tests_today = quiz_results.count_documents({"created_at": {"$gte": today_start}})
        tests_this_week = quiz_results.count_documents({"created_at": {"$gte": week_ago}})
        
        # Calculate average score
        pipeline = [
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ]
        avg_result = list(quiz_results.aggregate(pipeline))
        average_score = round(avg_result[0]["avg_score"], 1) if avg_result and avg_result[0].get("avg_score") else 0
        
        # Pass rate (score >= 60%)
        passed = quiz_results.count_documents({"score": {"$gte": 60}})
        pass_rate = round((passed / total_tests_taken * 100), 1) if total_tests_taken > 0 else 0
        
        # Question sets created
        question_sets = db.get_collection("question_sets")
        total_tests_created = question_sets.count_documents({})
        
        test_stats = {
            "total_tests_created": total_tests_created,
            "total_tests_taken": total_tests_taken,
            "tests_completed": total_tests_taken,
            "tests_in_progress": 0,
            "average_score": average_score,
            "pass_rate": pass_rate,
            "tests_today": tests_today,
            "tests_this_week": tests_this_week
        }
        
        # Activity Trend (last 14 days)
        activity_trend = []
        for i in range(13, -1, -1):
            date = today_start - timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            active_users = db.users.count_documents({
                "last_login": {"$gte": date, "$lt": next_date}
            })
            tests_taken = quiz_results.count_documents({
                "created_at": {"$gte": date, "$lt": next_date}
            })
            
            activity_trend.append({
                "date": date.strftime("%Y-%m-%d"),
                "active_users": active_users,
                "tests_taken": tests_taken
            })
        
        # Subject-wise Performance
        subject_pipeline = [
            {"$group": {
                "_id": "$subject",
                "avg_score": {"$avg": "$score"},
                "total_tests": {"$sum": 1},
                "total_students": {"$addToSet": "$student_id"}
            }},
            {"$project": {
                "subject": "$_id",
                "avg_score": {"$round": ["$avg_score", 1]},
                "total_tests": 1,
                "total_students": {"$size": "$total_students"}
            }}
        ]
        subject_stats = list(quiz_results.aggregate(subject_pipeline))
        
        # Top Performers
        performer_pipeline = [
            {"$group": {
                "_id": "$student_id",
                "avg_score": {"$avg": "$score"},
                "tests_completed": {"$sum": 1}
            }},
            {"$match": {"tests_completed": {"$gte": 1}}},
            {"$sort": {"avg_score": -1}},
            {"$limit": 5}
        ]
        top_performers_raw = list(quiz_results.aggregate(performer_pipeline))
        
        top_performers = []
        for p in top_performers_raw:
            student = db.users.find_one({"_id": ObjectId(p["_id"])} if ObjectId.is_valid(str(p["_id"])) else {"user_id": str(p["_id"])})
            top_performers.append({
                "student_id": str(p["_id"]),
                "name": student.get("name", "Unknown") if student else "Unknown",
                "avg_score": round(p["avg_score"], 1),
                "tests_completed": p["tests_completed"]
            })
        
        # Weak Students (low scores or inactive)
        weak_pipeline = [
            {"$group": {
                "_id": "$student_id",
                "avg_score": {"$avg": "$score"},
                "tests_completed": {"$sum": 1}
            }},
            {"$match": {"avg_score": {"$lt": 50}}},
            {"$sort": {"avg_score": 1}},
            {"$limit": 5}
        ]
        weak_students_raw = list(quiz_results.aggregate(weak_pipeline))
        
        weak_students = []
        for w in weak_students_raw:
            student = db.users.find_one({"_id": ObjectId(w["_id"])} if ObjectId.is_valid(str(w["_id"])) else {"user_id": str(w["_id"])})
            days_inactive = 0
            if student and student.get("last_login"):
                days_inactive = (now - student["last_login"]).days
            weak_students.append({
                "student_id": str(w["_id"]),
                "name": student.get("name", "Unknown") if student else "Unknown",
                "avg_score": round(w["avg_score"], 1),
                "days_inactive": days_inactive
            })
        
        # Recent Activities
        recent_pipeline = [
            {"$sort": {"created_at": -1}},
            {"$limit": 10},
            {"$project": {
                "student_id": 1,
                "subject": 1,
                "score": 1,
                "created_at": 1
            }}
        ]
        recent_activities = list(quiz_results.aggregate(recent_pipeline))
        
        return {
            "user_stats": user_stats,
            "test_stats": test_stats,
            "activity_trend": activity_trend,
            "subject_stats": subject_stats,
            "top_performers": top_performers,
            "weak_students": weak_students,
            "recent_activities": recent_activities
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        # Return empty data on error
        return {
            "user_stats": {
                "total_users": 0, "total_students": 0, "total_teachers": 0,
                "active_today": 0, "active_this_week": 0, "active_this_month": 0,
                "inactive_users": 0, "new_users_today": 0, "new_users_this_week": 0, "new_users_this_month": 0
            },
            "test_stats": {
                "total_tests_created": 0, "total_tests_taken": 0, "tests_completed": 0,
                "tests_in_progress": 0, "average_score": 0, "pass_rate": 0,
                "tests_today": 0, "tests_this_week": 0
            },
            "activity_trend": [],
            "subject_stats": [],
            "top_performers": [],
            "weak_students": [],
            "recent_activities": []
        }


# ==================== STUDENT MANAGEMENT ENDPOINTS ====================

@router.get("/students")
async def get_students(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    is_active: Optional[bool] = None,
    class_level: Optional[int] = None,
    search: Optional[str] = None
):
    """
    Get list of all students with optional filters.
    """
    try:
        # Build filter
        filter_query = {"role": "student"}
        
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        if class_level is not None:
            filter_query["class_level"] = class_level
        
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"user_id": {"$regex": search, "$options": "i"}}
            ]
        
        # Query students
        cursor = db.users.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
        students = [serialize_student(s) for s in cursor]
        
        return students
        
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students")
async def create_student(student: StudentCreate):
    """
    Create a new student account.
    Auto-generates user_id and password based on name and age.
    
    ID Format: {name}{age}{sequential_number} (e.g., sajith141)
    Password: {name}{age} (e.g., sajith14)
    """
    try:
        # Check if email already exists
        existing = db.users.find_one({"email": student.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate user_id and password
        user_id = generate_student_id(student.name, student.age)
        password = generate_password(student.name, student.age)
        hashed_password = hash_password(password)
        
        # Create student document (no preferred_subject - students access all subjects for their class)
        student_doc = {
            "user_id": user_id,
            "name": student.name,
            "age": student.age,
            "email": student.email,
            "mobile": student.mobile,
            "password": hashed_password,
            "role": "student",
            "class_level": student.class_level,
            "is_active": True,
            "isOnboarded": False,
            "created_at": datetime.utcnow(),
            "last_login": None,
            "tests_completed": 0,
            "avg_score": 0.0
        }
        
        # Insert into database
        result = db.users.insert_one(student_doc)
        student_doc["_id"] = result.inserted_id
        
        # Return with credentials
        response = serialize_student(student_doc)
        response["generated_credentials"] = {
            "user_id": user_id,
            "password": password,  # Plain text for admin to share
            "note": "Share these credentials with the student. They will be prompted to change password on first login."
        }
        
        logger.info(f"Created student: {user_id} ({student.name})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}")
async def get_student(student_id: str):
    """
    Get a single student by ID (MongoDB _id or user_id).
    """
    try:
        # Try as ObjectId first
        student = None
        if ObjectId.is_valid(student_id):
            student = db.users.find_one({"_id": ObjectId(student_id), "role": "student"})
        
        if not student:
            student = db.users.find_one({"user_id": student_id, "role": "student"})
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return serialize_student(student)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/students/{student_id}")
async def update_student(student_id: str, student: StudentUpdate):
    """
    Update a student's information.
    """
    try:
        # Build update document
        update_doc = {}
        if student.name is not None:
            update_doc["name"] = student.name
        if student.age is not None:
            update_doc["age"] = student.age
        if student.email is not None:
            update_doc["email"] = student.email
        if student.mobile is not None:
            update_doc["mobile"] = student.mobile
        if student.class_level is not None:
            update_doc["class_level"] = student.class_level
        if student.is_active is not None:
            update_doc["is_active"] = student.is_active
        
        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_doc["updated_at"] = datetime.utcnow()
        
        # Find and update
        query = {"_id": ObjectId(student_id), "role": "student"} if ObjectId.is_valid(student_id) else {"user_id": student_id, "role": "student"}
        result = db.users.find_one_and_update(
            query,
            {"$set": update_doc},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Student not found")
        
        logger.info(f"Updated student: {student_id}")
        return serialize_student(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/students/{student_id}")
async def delete_student(student_id: str):
    """
    Delete a student (soft delete by setting is_active=False, or hard delete).
    """
    try:
        # Find student
        query = {"_id": ObjectId(student_id), "role": "student"} if ObjectId.is_valid(student_id) else {"user_id": student_id, "role": "student"}
        
        # Hard delete
        result = db.users.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        
        logger.info(f"Deleted student: {student_id}")
        return {"success": True, "message": "Student deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students/{student_id}/reset-password")
async def reset_student_password(student_id: str):
    """
    Reset a student's password to the default (name + age).
    """
    try:
        # Find student
        query = {"_id": ObjectId(student_id), "role": "student"} if ObjectId.is_valid(student_id) else {"user_id": student_id, "role": "student"}
        student = db.users.find_one(query)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Generate new password
        new_password = generate_password(student.get("name", "student"), student.get("age", 10))
        hashed_password = hash_password(new_password)
        
        # Update password
        db.users.update_one(
            {"_id": student["_id"]},
            {"$set": {"password": hashed_password, "password_changed_at": None}}
        )
        
        logger.info(f"Reset password for student: {student_id}")
        return {
            "success": True,
            "message": "Password reset successfully",
            "new_password": new_password,
            "note": "Share this password with the student"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TEACHER MANAGEMENT ENDPOINTS ====================

@router.get("/teachers")
async def get_teachers(
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = None
):
    """
    Get list of all teachers.
    """
    try:
        filter_query = {"role": "teacher"}
        
        if is_active is not None:
            filter_query["is_active"] = is_active
        
        cursor = db.users.find(filter_query).limit(limit).sort("created_at", -1)
        teachers = []
        
        for t in cursor:
            teachers.append({
                "id": str(t.get("_id", "")),
                "user_id": t.get("user_id", ""),
                "name": t.get("name", ""),
                "email": t.get("email", ""),
                "is_active": t.get("is_active", True),
                "created_at": t.get("created_at", datetime.utcnow()).isoformat() if t.get("created_at") else None,
                "last_login": t.get("last_login").isoformat() if t.get("last_login") else None
            })
        
        return teachers
        
    except Exception as e:
        logger.error(f"Error fetching teachers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
