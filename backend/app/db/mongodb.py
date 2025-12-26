"""
MongoDB Connection and Operations
Migrated from Django ncert_project/mongodb_utils.py
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

logger = logging.getLogger(__name__)

# Global MongoDB client
_mongo_client: Optional[AsyncIOMotorClient] = None
_db = None


async def init_mongodb():
    """Initialize async MongoDB connection"""
    global _mongo_client, _db
    
    try:
        # MongoDB Atlas connection with SSL settings
        # Note: tlsAllowInvalidCertificates is for development only
        _mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
            retryWrites=True,
            tls=True,
            tlsAllowInvalidCertificates=True,  # For development - disable in production
        )
        _db = _mongo_client[settings.MONGODB_DB_NAME]
        
        # Test connection
        for attempt in range(3):
            try:
                await _mongo_client.admin.command('ping')
                break
            except Exception as e:
                if attempt < 2:
                    logger.warning(f"MongoDB connection attempt {attempt + 1} failed, retrying...")
                    import asyncio
                    await asyncio.sleep(1)
                else:
                    raise
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"MongoDB connected to database: {settings.MONGODB_DB_NAME}")
        
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}")
        _mongo_client = None
        _db = None


async def close_mongodb():
    """Close MongoDB connection"""
    global _mongo_client, _db
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _db = None
        logger.info("MongoDB connection closed")


async def check_mongodb_health() -> str:
    """Check MongoDB connection health"""
    global _db
    try:
        if _mongo_client is None or _db is None:
            return "disconnected"
        await _mongo_client.admin.command('ping')
        return "connected"
    except Exception as e:
        return f"error: {str(e)}"


async def create_indexes():
    """Create necessary indexes for performance"""
    if _db is None:
        return
    
    try:
        # Users collection
        await _db.users.create_index("username", unique=True)
        await _db.users.create_index("email", unique=True)
        
        # Chat history
        await _db.chat_history.create_index([("user_id", 1), ("created_at", -1)])
        await _db.chat_history.create_index("conversation_id")
        
        # Chat cache
        await _db.chat_cache.create_index("question_hash", unique=True)
        await _db.chat_cache.create_index("expires_at", expireAfterSeconds=0)
        
        # Quiz attempts
        await _db.quiz_attempts.create_index([("user_id", 1), ("quiz_id", 1)])
        
        # Book chapters
        await _db.book_chapters.create_index([("class_num", 1), ("subject", 1)])
        
        logger.info("MongoDB indexes created")
    except Exception as e:
        logger.warning(f"Index creation failed: {e}")


async def ensure_connected():
    """Ensure MongoDB is connected, reconnect if needed"""
    global _db
    if _db is None:
        await init_mongodb()
    return _db is not None


def get_db():
    """Get database instance"""
    if _db is None:
        raise RuntimeError("MongoDB not connected. Please check your MONGODB_URI in .env")
    return _db


def is_db_connected() -> bool:
    """Check if database is connected"""
    return _db is not None


# ==================== USER OPERATIONS ====================

async def create_user(user_data: Dict) -> str:
    """Create a new user"""
    await ensure_connected()
    if not is_db_connected():
        raise RuntimeError("MongoDB not connected")
    db = get_db()
    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    result = await db.users.insert_one(user_data)
    return str(result.inserted_id)


async def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username"""
    await ensure_connected()
    if not is_db_connected():
        return None
    db = get_db()
    return await db.users.find_one({"username": username})


async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    await ensure_connected()
    if not is_db_connected():
        return None
    from bson import ObjectId
    db = get_db()
    return await db.users.find_one({"_id": ObjectId(user_id)})


# ==================== CHAT OPERATIONS ====================

async def save_chat(
    user_id: str,
    question: str,
    answer: str,
    conversation_id: str,
    model_used: str = "gemini",
    sources: Optional[List[Dict]] = None,
    language: str = "en",
    response_time_ms: int = 0
) -> str:
    """Save chat message to MongoDB"""
    db = get_db()
    
    chat_doc = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer,
        "model_used": model_used,
        "sources": sources or [],
        "language": language,
        "response_time_ms": response_time_ms,
        "created_at": datetime.utcnow()
    }
    
    result = await db.chat_history.insert_one(chat_doc)
    return str(result.inserted_id)


async def get_chat_history(
    user_id: str,
    conversation_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
) -> List[Dict]:
    """Get user's chat history"""
    db = get_db()
    
    query = {"user_id": user_id}
    if conversation_id:
        query["conversation_id"] = conversation_id
    
    cursor = db.chat_history.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def get_conversation_context(conversation_id: str, limit: int = 5) -> List[Dict]:
    """Get recent messages from a conversation for context"""
    db = get_db()
    cursor = db.chat_history.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", -1).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    return list(reversed(messages))  # Return in chronological order


# ==================== CACHE OPERATIONS ====================

async def get_cached_response(question_hash: str) -> Optional[Dict]:
    """Get cached response for a question"""
    db = get_db()
    cache = await db.chat_cache.find_one({
        "question_hash": question_hash,
        "is_valid": True
    })
    return cache


async def set_cached_response(
    question_hash: str,
    question: str,
    answer: str,
    sources: List[Dict],
    ttl_seconds: int = None
) -> str:
    """Cache a response"""
    db = get_db()
    
    ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
    expires_at = datetime.utcnow()
    
    from datetime import timedelta
    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
    
    cache_doc = {
        "question_hash": question_hash,
        "question": question,
        "answer": answer,
        "sources": sources,
        "is_valid": True,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "hit_count": 0
    }
    
    result = await db.chat_cache.replace_one(
        {"question_hash": question_hash},
        cache_doc,
        upsert=True
    )
    
    return str(result.upserted_id) if result.upserted_id else "updated"


async def invalidate_cache(question_hash: str):
    """Invalidate a cached response (wrong answer reported)"""
    db = get_db()
    await db.chat_cache.update_one(
        {"question_hash": question_hash},
        {"$set": {"is_valid": False}}
    )


# ==================== QUIZ OPERATIONS ====================

async def save_quiz_attempt(attempt_data: Dict) -> str:
    """Save quiz attempt"""
    db = get_db()
    attempt_data["created_at"] = datetime.utcnow()
    result = await db.quiz_attempts.insert_one(attempt_data)
    return str(result.inserted_id)


async def get_quiz_attempts(user_id: str, quiz_id: Optional[str] = None) -> List[Dict]:
    """Get user's quiz attempts"""
    db = get_db()
    query = {"user_id": user_id}
    if quiz_id:
        query["quiz_id"] = quiz_id
    cursor = db.quiz_attempts.find(query).sort("created_at", -1)
    return await cursor.to_list(length=100)


# ==================== BOOK/CHAPTER OPERATIONS ====================

async def get_book_chapters(
    class_num: Optional[str] = None,
    subject: Optional[str] = None
) -> List[Dict]:
    """Get book chapters with optional filters"""
    db = get_db()
    query = {}
    if class_num:
        query["class_num"] = class_num
    if subject:
        query["subject"] = subject
    
    cursor = db.book_chapters.find(query).sort([("class_num", 1), ("chapter_order", 1)])
    return await cursor.to_list(length=500)


async def save_book_chapter(chapter_data: Dict) -> str:
    """Save book chapter metadata"""
    db = get_db()
    chapter_data["created_at"] = datetime.utcnow()
    result = await db.book_chapters.insert_one(chapter_data)
    return str(result.inserted_id)


# ==================== ANALYTICS ====================

async def get_user_analytics(user_id: str) -> Dict:
    """Get comprehensive user analytics"""
    db = get_db()
    
    # Chat stats
    chat_count = await db.chat_history.count_documents({"user_id": user_id})
    
    # Quiz stats
    quiz_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_quizzes": {"$sum": 1},
            "avg_score": {"$avg": "$score"},
            "total_questions": {"$sum": "$total_questions"}
        }}
    ]
    quiz_stats = await db.quiz_attempts.aggregate(quiz_pipeline).to_list(1)
    
    return {
        "total_chats": chat_count,
        "quiz_stats": quiz_stats[0] if quiz_stats else {},
    }
