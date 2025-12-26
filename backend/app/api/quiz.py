"""
Quiz API Routes
Quiz system endpoints for student assessments
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.auth import get_current_active_user
from app.db.models import (
    QuizQuestion, QuizSubmission, QuizResult, 
    DifficultyLevel
)
from app.db.mongodb import (
    get_db, save_quiz_attempt, get_quiz_attempts
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chapters")
async def get_available_chapters(
    grade: Optional[int] = Query(None, ge=5, le=12),
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get available chapters for quiz"""
    db = get_db()
    
    query = {"is_active": True}
    if grade:
        query["class_num"] = str(grade)
    if subject:
        query["subject"] = subject
    
    chapters = await db.quiz_chapters.find(query).to_list(100)
    
    return {
        "chapters": [
            {
                "id": str(ch["_id"]),
                "chapter_id": ch.get("chapter_id"),
                "class_num": ch.get("class_num"),
                "subject": ch.get("subject"),
                "chapter_name": ch.get("chapter_name"),
                "total_questions": ch.get("total_questions", 10)
            }
            for ch in chapters
        ]
    }


@router.get("/questions/{chapter_id}")
async def get_quiz_questions(
    chapter_id: str,
    count: int = Query(10, ge=5, le=20),
    difficulty: Optional[DifficultyLevel] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get quiz questions for a chapter"""
    db = get_db()
    
    query = {"chapter_id": chapter_id, "is_active": True}
    if difficulty:
        query["difficulty"] = difficulty.value
    
    # Get random questions
    pipeline = [
        {"$match": query},
        {"$sample": {"size": count}}
    ]
    
    questions = await db.quiz_questions.aggregate(pipeline).to_list(count)
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this chapter")
    
    # Format questions (hide correct answer)
    formatted = []
    for q in questions:
        formatted.append({
            "id": str(q["_id"]),
            "question": q.get("question"),
            "options": q.get("options", []),
            "difficulty": q.get("difficulty", "medium"),
            "chapter": q.get("chapter_name", "")
        })
    
    return {"questions": formatted}


@router.post("/submit", response_model=QuizResult)
async def submit_quiz(
    submission: QuizSubmission,
    current_user: dict = Depends(get_current_active_user)
):
    """Submit quiz answers and get results"""
    db = get_db()
    user_id = str(current_user["_id"])
    
    # Get correct answers
    question_ids = [a.question_id for a in submission.answers]
    from bson import ObjectId
    
    questions = await db.quiz_questions.find({
        "_id": {"$in": [ObjectId(qid) for qid in question_ids]}
    }).to_list(len(question_ids))
    
    correct_answers = {str(q["_id"]): q.get("correct_answer", 0) for q in questions}
    
    # Calculate score
    correct_count = 0
    total_time = 0
    chapter_results = {}
    
    for answer in submission.answers:
        total_time += answer.time_taken_seconds
        correct_answer = correct_answers.get(answer.question_id)
        is_correct = answer.selected_answer == correct_answer
        
        if is_correct:
            correct_count += 1
        
        # Track by chapter
        q = next((q for q in questions if str(q["_id"]) == answer.question_id), None)
        if q:
            chapter = q.get("chapter_name", "Unknown")
            if chapter not in chapter_results:
                chapter_results[chapter] = {"correct": 0, "total": 0}
            chapter_results[chapter]["total"] += 1
            if is_correct:
                chapter_results[chapter]["correct"] += 1
    
    total_questions = len(submission.answers)
    percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    passed = percentage >= 70
    
    # Save attempt
    attempt_data = {
        "user_id": user_id,
        "quiz_id": submission.quiz_id,
        "score": correct_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "passed": passed,
        "time_taken_seconds": total_time,
        "chapter_analysis": chapter_results,
        "answers": [a.model_dump() for a in submission.answers]
    }
    
    await save_quiz_attempt(attempt_data)
    
    return QuizResult(
        quiz_id=submission.quiz_id,
        score=correct_count,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
        time_taken_seconds=total_time,
        chapter_analysis=chapter_results
    )


@router.get("/history")
async def get_quiz_history(
    limit: int = Query(20, le=100),
    current_user: dict = Depends(get_current_active_user)
):
    """Get user's quiz attempt history"""
    user_id = str(current_user["_id"])
    
    attempts = await get_quiz_attempts(user_id)
    
    return {
        "attempts": [
            {
                "id": str(a.get("_id")),
                "quiz_id": a.get("quiz_id"),
                "score": a.get("score"),
                "total": a.get("total_questions"),
                "percentage": a.get("percentage"),
                "passed": a.get("passed"),
                "time_seconds": a.get("time_taken_seconds"),
                "created_at": a.get("created_at")
            }
            for a in attempts[:limit]
        ]
    }


@router.get("/analytics")
async def get_quiz_analytics(
    current_user: dict = Depends(get_current_active_user)
):
    """Get comprehensive quiz analytics for user"""
    db = get_db()
    user_id = str(current_user["_id"])
    
    # Aggregate quiz performance
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_quizzes": {"$sum": 1},
            "total_correct": {"$sum": "$score"},
            "total_questions": {"$sum": "$total_questions"},
            "avg_percentage": {"$avg": "$percentage"},
            "total_time": {"$sum": "$time_taken_seconds"},
            "passed_count": {"$sum": {"$cond": ["$passed", 1, 0]}}
        }}
    ]
    
    result = await db.quiz_attempts.aggregate(pipeline).to_list(1)
    
    if not result:
        return {
            "total_quizzes": 0,
            "average_score": 0,
            "pass_rate": 0,
            "total_time_minutes": 0
        }
    
    stats = result[0]
    return {
        "total_quizzes": stats.get("total_quizzes", 0),
        "average_score": round(stats.get("avg_percentage", 0), 1),
        "pass_rate": round(stats.get("passed_count", 0) / max(stats.get("total_quizzes", 1), 1) * 100, 1),
        "total_time_minutes": round(stats.get("total_time", 0) / 60, 1),
        "total_questions_attempted": stats.get("total_questions", 0)
    }
