"""
Support Router
- FAQ management
- Contact information
- Help documentation
- General support utilities
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import logging

from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/support", tags=["Support"])


# ==================== PYDANTIC MODELS ====================

class FAQCreate(BaseModel):
    """Model for creating an FAQ."""
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(default="general")
    order: int = Field(default=0)


class FAQUpdate(BaseModel):
    """Model for updating an FAQ."""
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


class ContactMessage(BaseModel):
    """Model for contact form submission."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=200)
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class FeedbackSubmission(BaseModel):
    """Model for feedback submission."""
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = Field(default="general", description="general, bug, feature, content")
    message: str = Field(..., min_length=10, max_length=5000)
    page: Optional[str] = None


# ==================== FAQ ENDPOINTS ====================

@router.get("/faqs")
async def get_faqs(
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True
):
    """
    Get list of FAQs.
    """
    try:
        filter_query = {"is_active": is_active}
        
        if category:
            filter_query["category"] = category
        
        if search:
            filter_query["$or"] = [
                {"question": {"$regex": search, "$options": "i"}},
                {"answer": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = db.get_collection("faqs").find(filter_query).sort("order", 1)
        faqs = []
        
        for faq in cursor:
            faqs.append({
                "id": str(faq.get("_id", "")),
                "question": faq.get("question", ""),
                "answer": faq.get("answer", ""),
                "category": faq.get("category", "general"),
                "order": faq.get("order", 0),
                "is_active": faq.get("is_active", True),
                "views": faq.get("views", 0),
                "helpful_count": faq.get("helpful_count", 0)
            })
        
        return faqs
        
    except Exception as e:
        logger.error(f"Error fetching FAQs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faqs")
async def create_faq(faq: FAQCreate):
    """
    Create a new FAQ (admin only).
    """
    try:
        faq_doc = {
            "question": faq.question,
            "answer": faq.answer,
            "category": faq.category,
            "order": faq.order,
            "is_active": True,
            "views": 0,
            "helpful_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = db.get_collection("faqs").insert_one(faq_doc)
        faq_doc["_id"] = result.inserted_id
        
        logger.info(f"Created FAQ: {faq.question[:50]}...")
        return {
            "id": str(faq_doc["_id"]),
            "question": faq_doc["question"],
            "answer": faq_doc["answer"],
            "category": faq_doc["category"],
            "order": faq_doc["order"]
        }
        
    except Exception as e:
        logger.error(f"Error creating FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/faqs/{faq_id}")
async def update_faq(faq_id: str, faq: FAQUpdate):
    """
    Update an FAQ (admin only).
    """
    try:
        update_doc = {}
        
        if faq.question is not None:
            update_doc["question"] = faq.question
        if faq.answer is not None:
            update_doc["answer"] = faq.answer
        if faq.category is not None:
            update_doc["category"] = faq.category
        if faq.order is not None:
            update_doc["order"] = faq.order
        if faq.is_active is not None:
            update_doc["is_active"] = faq.is_active
        
        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_doc["updated_at"] = datetime.utcnow()
        
        result = db.get_collection("faqs").find_one_and_update(
            {"_id": ObjectId(faq_id)},
            {"$set": update_doc},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        return {
            "id": str(result["_id"]),
            "question": result["question"],
            "answer": result["answer"],
            "category": result["category"],
            "order": result["order"],
            "is_active": result["is_active"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: str):
    """
    Delete an FAQ (admin only).
    """
    try:
        result = db.get_collection("faqs").delete_one({"_id": ObjectId(faq_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        return {"success": True, "message": "FAQ deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting FAQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faqs/{faq_id}/helpful")
async def mark_faq_helpful(faq_id: str):
    """
    Mark an FAQ as helpful (increment counter).
    """
    try:
        result = db.get_collection("faqs").update_one(
            {"_id": ObjectId(faq_id)},
            {"$inc": {"helpful_count": 1}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        return {"success": True, "message": "Marked as helpful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking FAQ helpful: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faqs/{faq_id}/view")
async def increment_faq_views(faq_id: str):
    """
    Increment view count for an FAQ.
    """
    try:
        db.get_collection("faqs").update_one(
            {"_id": ObjectId(faq_id)},
            {"$inc": {"views": 1}}
        )
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error incrementing FAQ views: {e}")
        return {"success": False}


# ==================== CONTACT ENDPOINTS ====================

@router.post("/contact")
async def submit_contact_message(message: ContactMessage):
    """
    Submit a contact form message.
    """
    try:
        message_doc = {
            "name": message.name,
            "email": message.email,
            "subject": message.subject,
            "message": message.message,
            "status": "new",
            "created_at": datetime.utcnow(),
            "responded_at": None,
            "response": None
        }
        
        result = db.get_collection("contact_messages").insert_one(message_doc)
        
        logger.info(f"New contact message from: {message.email}")
        return {
            "success": True,
            "message": "Your message has been received. We will get back to you soon.",
            "reference_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Error submitting contact message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contact/messages")
async def get_contact_messages(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all contact messages (admin only).
    """
    try:
        filter_query = {}
        if status:
            filter_query["status"] = status
        
        cursor = db.get_collection("contact_messages").find(filter_query).sort("created_at", -1).limit(limit)
        messages = []
        
        for msg in cursor:
            messages.append({
                "id": str(msg.get("_id", "")),
                "name": msg.get("name", ""),
                "email": msg.get("email", ""),
                "subject": msg.get("subject", ""),
                "message": msg.get("message", ""),
                "status": msg.get("status", "new"),
                "created_at": msg.get("created_at", datetime.utcnow()).isoformat(),
                "responded_at": msg.get("responded_at").isoformat() if msg.get("responded_at") else None,
                "response": msg.get("response")
            })
        
        return messages
        
    except Exception as e:
        logger.error(f"Error fetching contact messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FEEDBACK ENDPOINTS ====================

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackSubmission,
    user_id: Optional[str] = None
):
    """
    Submit user feedback.
    """
    try:
        feedback_doc = {
            "user_id": user_id,
            "rating": feedback.rating,
            "feedback_type": feedback.feedback_type,
            "message": feedback.message,
            "page": feedback.page,
            "status": "new",
            "created_at": datetime.utcnow()
        }
        
        result = db.get_collection("feedback").insert_one(feedback_doc)
        
        logger.info(f"New feedback submitted: {feedback.feedback_type} - {feedback.rating}/5")
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "feedback_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback")
async def get_feedback(
    feedback_type: Optional[str] = None,
    min_rating: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all feedback (admin only).
    """
    try:
        filter_query = {}
        
        if feedback_type:
            filter_query["feedback_type"] = feedback_type
        
        if min_rating:
            filter_query["rating"] = {"$gte": min_rating}
        
        cursor = db.get_collection("feedback").find(filter_query).sort("created_at", -1).limit(limit)
        feedback_list = []
        
        for fb in cursor:
            feedback_list.append({
                "id": str(fb.get("_id", "")),
                "user_id": fb.get("user_id"),
                "rating": fb.get("rating", 0),
                "feedback_type": fb.get("feedback_type", "general"),
                "message": fb.get("message", ""),
                "page": fb.get("page"),
                "status": fb.get("status", "new"),
                "created_at": fb.get("created_at", datetime.utcnow()).isoformat()
            })
        
        return feedback_list
        
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats")
async def get_feedback_stats():
    """
    Get feedback statistics (admin only).
    """
    try:
        collection = db.get_collection("feedback")
        
        total = collection.count_documents({})
        
        # Average rating
        pipeline = [{"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}]
        avg_result = list(collection.aggregate(pipeline))
        avg_rating = round(avg_result[0]["avg_rating"], 2) if avg_result and avg_result[0].get("avg_rating") else 0
        
        # Rating distribution
        rating_pipeline = [
            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        ratings = {str(r["_id"]): r["count"] for r in collection.aggregate(rating_pipeline)}
        
        # Type distribution
        type_pipeline = [
            {"$group": {"_id": "$feedback_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        types = list(collection.aggregate(type_pipeline))
        
        return {
            "total": total,
            "average_rating": avg_rating,
            "rating_distribution": ratings,
            "type_distribution": types
        }
        
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELP DOCUMENTATION ====================

@router.get("/help")
async def get_help_topics():
    """
    Get help documentation topics.
    """
    # Static help documentation
    return {
        "topics": [
            {
                "id": "getting-started",
                "title": "Getting Started",
                "description": "Learn how to use the NCERT Learning Platform",
                "sections": [
                    {"title": "Login", "content": "Use your student ID and password to login. First-time users will be prompted to change their password."},
                    {"title": "Dashboard", "content": "The dashboard shows your progress, streaks, and quick access to all features."},
                    {"title": "Book to Bot", "content": "Read NCERT textbooks and get AI-powered explanations for any text."}
                ]
            },
            {
                "id": "tests",
                "title": "Tests & Quizzes",
                "description": "How to take tests and view results",
                "sections": [
                    {"title": "Taking a Test", "content": "Go to Test Center, select a test, and answer all questions within the time limit."},
                    {"title": "Viewing Results", "content": "After completing a test, you can view detailed results with correct answers and explanations."},
                    {"title": "Report Card", "content": "View your overall performance across all tests in the Report Card section."}
                ]
            },
            {
                "id": "ai-features",
                "title": "AI Features",
                "description": "Using AI-powered learning tools",
                "sections": [
                    {"title": "AI Chat", "content": "Ask questions about any topic and get detailed explanations from the AI assistant."},
                    {"title": "Text Annotations", "content": "Select text in the PDF viewer to get definitions, explanations, or create sticky notes."},
                    {"title": "Quick vs DeepDive", "content": "Quick mode gives concise answers. DeepDive mode provides detailed explanations with examples."}
                ]
            },
            {
                "id": "account",
                "title": "Account Settings",
                "description": "Managing your account",
                "sections": [
                    {"title": "Profile", "content": "Update your name, email, and other profile information in Settings."},
                    {"title": "Password", "content": "Change your password in the Account Security section of Settings."},
                    {"title": "Preferences", "content": "Set your preferred subject and class level for personalized content."}
                ]
            }
        ],
        "contact": {
            "email": "support@ncertlearning.com",
            "hours": "Monday - Friday, 9 AM - 6 PM IST"
        }
    }


# ==================== SYSTEM STATUS ====================

@router.get("/status")
async def get_system_status():
    """
    Get system status and announcements.
    """
    try:
        # Check database connectivity
        db_status = "operational"
        try:
            db.users.find_one({})
        except Exception:
            db_status = "degraded"
        
        return {
            "status": "operational" if db_status == "operational" else "degraded",
            "services": {
                "database": db_status,
                "ai_chat": "operational",
                "pdf_viewer": "operational",
                "tests": "operational"
            },
            "announcements": [],
            "maintenance": None,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "last_updated": datetime.utcnow().isoformat()
        }
