"""
Admin API Routes
Superadmin dashboard and management endpoints
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.api.auth import get_current_active_user, require_role
from app.db.mongodb import get_db, get_user_analytics
from app.db.pinecone import get_stats as get_pinecone_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard")
async def admin_dashboard(
    current_user: dict = Depends(require_role("super_admin"))
):
    """Get admin dashboard statistics with comprehensive analytics"""
    db = get_db()
    
    # Count users
    total_users = await db.users.count_documents({})
    active_students = await db.users.count_documents({"role": "student", "is_active": True})
    
    # Count chats
    total_chats = await db.chat_history.count_documents({})
    
    # Count quizzes
    total_quiz_attempts = await db.quiz_attempts.count_documents({})
    
    # Count uploaded books
    total_books = await db.uploaded_books.count_documents({})
    processed_books = await db.uploaded_books.count_documents({"status": "completed"})
    
    # Get vector database stats
    vector_stats = await get_pinecone_stats()
    
    # Class-wise student distribution
    class_pipeline = [
        {"$match": {"role": "student"}},
        {"$group": {"_id": "$grade", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    class_distribution = await db.users.aggregate(class_pipeline).to_list(20)
    class_analytics = [
        {"class": f"Class {item['_id'] or 'Unknown'}", "students": item["count"]}
        for item in class_distribution
    ]
    
    # Subject-wise performance (from quiz attempts)
    subject_pipeline = [
        {"$group": {
            "_id": "$subject",
            "avgScore": {"$avg": "$percentage"},
            "totalAttempts": {"$sum": 1},
            "students": {"$addToSet": "$user_id"}
        }},
        {"$project": {
            "subject": "$_id",
            "avgScore": {"$round": ["$avgScore", 1]},
            "totalAttempts": 1,
            "students": {"$size": "$students"}
        }},
        {"$sort": {"totalAttempts": -1}}
    ]
    subject_stats = await db.quiz_attempts.aggregate(subject_pipeline).to_list(20)
    subject_analytics = [
        {
            "subject": item.get("subject") or "General",
            "avgScore": item.get("avgScore") or 0,
            "totalAttempts": item.get("totalAttempts") or 0,
            "students": item.get("students") or 0
        }
        for item in subject_stats
    ]
    
    # Top performers
    top_pipeline = [
        {"$group": {
            "_id": "$user_id",
            "avgScore": {"$avg": "$percentage"},
            "quizzes": {"$sum": 1}
        }},
        {"$match": {"quizzes": {"$gte": 1}}},
        {"$sort": {"avgScore": -1}},
        {"$limit": 5}
    ]
    top_performers_raw = await db.quiz_attempts.aggregate(top_pipeline).to_list(5)
    
    # Enrich with user data
    top_performers = []
    for performer in top_performers_raw:
        from bson import ObjectId
        try:
            user = await db.users.find_one({"_id": ObjectId(performer["_id"])})
            if user:
                top_performers.append({
                    "name": user.get("full_name") or user.get("username") or "Unknown",
                    "class": user.get("grade"),
                    "avgScore": round(performer.get("avgScore") or 0, 1),
                    "quizzes": performer.get("quizzes") or 0
                })
        except:
            pass
    
    # Recent activity
    recent_chats = await db.chat_history.find().sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "users": {
            "total": total_users,
            "active_students": active_students
        },
        "chats": {
            "total": total_chats
        },
        "quizzes": {
            "total_attempts": total_quiz_attempts
        },
        "books": {
            "total": total_books,
            "processed": processed_books
        },
        "vector_db": vector_stats,
        "class_analytics": class_analytics,
        "subject_analytics": subject_analytics,
        "top_performers": top_performers,
        "recent_activity": [
            {
                "type": "chat",
                "question": chat.get("question", "")[:100],
                "created_at": chat.get("created_at")
            }
            for chat in recent_chats
        ]
    }


@router.get("/students")
async def list_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(require_role("super_admin"))
):
    """List all students with pagination"""
    db = get_db()
    
    query = {"role": "student"}
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * per_page
    
    students = await db.users.find(query).skip(skip).limit(per_page).to_list(per_page)
    total = await db.users.count_documents(query)
    
    return {
        "students": [
            {
                "id": str(s["_id"]),
                "username": s.get("username"),
                "email": s.get("email"),
                "full_name": s.get("full_name"),
                "grade": s.get("grade"),
                "created_at": s.get("created_at")
            }
            for s in students
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/students/{student_id}/analytics")
async def get_student_analytics(
    student_id: str,
    current_user: dict = Depends(require_role("super_admin"))
):
    """Get detailed analytics for a specific student"""
    analytics = await get_user_analytics(student_id)
    return analytics


@router.get("/books")
async def list_uploaded_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, le=100),
    status: Optional[str] = None,
    current_user: dict = Depends(require_role("super_admin"))
):
    """List all uploaded books"""
    db = get_db()
    
    query = {}
    if status:
        query["status"] = status
    
    skip = (page - 1) * per_page
    
    books = await db.uploaded_books.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(per_page)
    total = await db.uploaded_books.count_documents(query)
    
    return {
        "books": [
            {
                "id": str(b["_id"]),
                "filename": b.get("filename"),
                "class_num": b.get("class_num"),
                "subject": b.get("subject"),
                "status": b.get("status"),
                "chunks_count": b.get("chunks_count", 0),
                "created_at": b.get("created_at")
            }
            for b in books
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.delete("/books/{book_id}")
async def delete_book(
    book_id: str,
    current_user: dict = Depends(require_role("super_admin"))
):
    """Delete an uploaded book and its vectors"""
    from bson import ObjectId
    from bson.errors import InvalidId
    from app.db.pinecone import delete_by_source
    
    db = get_db()
    
    # Try to find book - support both UUID strings and ObjectId
    book = None
    
    # First try with string _id (UUID format used by upload)
    book = await db.uploaded_books.find_one({"_id": book_id})
    
    # If not found, try with ObjectId format
    if not book:
        try:
            book = await db.uploaded_books.find_one({"_id": ObjectId(book_id)})
        except InvalidId:
            pass  # Not a valid ObjectId, that's fine
    
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Delete from Pinecone (with subject for proper namespace)
    source_file = book.get("filename")
    subject = book.get("subject")
    if source_file:
        try:
            await delete_by_source(source_file, subject)
        except Exception as e:
            logger.warning(f"Failed to delete from Pinecone: {e}")
    
    # Delete from MongoDB using the actual _id from the found book
    await db.uploaded_books.delete_one({"_id": book["_id"]})
    
    # Delete related chapters
    if source_file:
        await db.book_chapters.delete_many({"source_file": source_file})
    
    return {"status": "success", "message": f"Deleted book: {source_file}"}


@router.get("/questions")
async def list_questions(
    class_num: Optional[str] = None,
    subject: Optional[str] = None,
    chapter: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, le=200),
    current_user: dict = Depends(require_role("super_admin"))
):
    """List questions from the question bank"""
    db = get_db()
    
    query = {}
    if class_num:
        query["class_num"] = class_num
    if subject:
        query["subject"] = subject
    if chapter:
        query["chapter_id"] = chapter
    
    skip = (page - 1) * per_page
    
    questions = await db.questions.find(query).skip(skip).limit(per_page).to_list(per_page)
    total = await db.questions.count_documents(query)
    
    return {
        "questions": [
            {
                "id": str(q["_id"]),
                "question": q.get("question"),
                "answer": q.get("answer"),
                "class_num": q.get("class_num"),
                "subject": q.get("subject"),
                "chapter": q.get("chapter_name"),
                "marks": q.get("marks", 1)
            }
            for q in questions
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(require_role("super_admin"))
):
    """Get cache statistics"""
    db = get_db()
    
    total_cached = await db.chat_cache.count_documents({})
    valid_cached = await db.chat_cache.count_documents({"is_valid": True})
    
    # Get hit counts
    pipeline = [
        {"$group": {
            "_id": None,
            "total_hits": {"$sum": "$hit_count"}
        }}
    ]
    hits = await db.chat_cache.aggregate(pipeline).to_list(1)
    
    return {
        "total_entries": total_cached,
        "valid_entries": valid_cached,
        "invalidated": total_cached - valid_cached,
        "total_hits": hits[0].get("total_hits", 0) if hits else 0
    }
