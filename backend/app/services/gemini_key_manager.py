"""
Gemini API Key Manager - Handles rotation of multiple API keys with quota tracking.

This service manages multiple Gemini API keys to overcome free tier limits:
- Each key has 20 requests/day limit
- Automatic rotation when quota exhausted
- Tracks usage in MongoDB
- Auto-resets at midnight Pacific Time
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from pymongo import MongoClient
from app.core.config import settings
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Pacific timezone for quota reset (Google's reset time)
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')


class GeminiKeyManager:
    """Manages multiple Gemini API keys with automatic rotation and quota tracking."""
    
    def __init__(self):
        self.keys: List[Dict] = []
        self.current_key_index = 0
        self.daily_limit = 20  # Free tier limit per key
        self.db = None
        
        # Load API keys from environment
        self._load_keys_from_env()
        
        # Initialize MongoDB connection for tracking
        self._init_db()
        
        logger.info(f"🔑 Gemini Key Manager initialized with {len(self.keys)} API keys")
        logger.info(f"📊 Total daily capacity: {len(self.keys) * self.daily_limit} requests")
    
    def _load_keys_from_env(self):
        """Load all GEMINI_API_KEY_* from environment variables."""
        for i in range(1, 11):  # Support up to 10 keys
            key_name = f"GEMINI_API_KEY_{i}"
            api_key = os.getenv(key_name)
            
            if api_key and api_key != "YOUR_SECOND_KEY_HERE":  # Skip placeholder values
                self.keys.append({
                    "id": key_name,
                    "key": api_key,
                    "index": i - 1
                })
                logger.info(f"✅ Loaded {key_name} (ending in ...{api_key[-6:]})")
        
        if not self.keys:
            # Fallback to legacy single key
            legacy_key = os.getenv("GEMINI_API_KEY")
            if legacy_key:
                self.keys.append({
                    "id": "GEMINI_API_KEY",
                    "key": legacy_key,
                    "index": 0
                })
                logger.warning("⚠️  Using legacy single API key. Add GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc. for rotation.")
        
        if not self.keys:
            raise ValueError("❌ No Gemini API keys found in environment variables!")
    
    def _init_db(self):
        """Initialize MongoDB connection for quota tracking."""
        try:
            client = MongoClient(settings.MONGO_URI)
            # Extract DB name from settings or use default
            db_name = "ncert_learning_db"  # Default database name
            self.db = client[db_name]
            self.quota_collection = self.db["gemini_quota_tracker"]
            
            # Ensure indexes
            self.quota_collection.create_index("key_id", unique=True)
            
            logger.info("✅ MongoDB connection initialized for quota tracking")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB for quota tracking: {e}")
            self.db = None
    
    def _get_current_pacific_date(self) -> str:
        """Get current date in Pacific timezone (for quota reset)."""
        return datetime.now(PACIFIC_TZ).strftime("%Y-%m-%d")
    
    def _get_quota_data(self, key_id: str) -> Dict:
        """Get quota data for a specific key from MongoDB."""
        if self.db is None:
            return {"request_count": 0, "date": self._get_current_pacific_date()}
        
        data = self.quota_collection.find_one({"key_id": key_id})
        
        if not data:
            # Initialize new key entry
            data = {
                "key_id": key_id,
                "request_count": 0,
                "date": self._get_current_pacific_date(),
                "last_used": None
            }
            self.quota_collection.insert_one(data)
        
        # Check if date changed (quota reset at midnight PT)
        current_date = self._get_current_pacific_date()
        if data["date"] != current_date:
            logger.info(f"🔄 Quota reset for {key_id} (new day: {current_date})")
            data["request_count"] = 0
            data["date"] = current_date
            self.quota_collection.update_one(
                {"key_id": key_id},
                {"$set": {"request_count": 0, "date": current_date}}
            )
        
        return data
    
    def _increment_usage(self, key_id: str):
        """Increment usage counter for a key."""
        if self.db is None:
            return
        
        current_date = self._get_current_pacific_date()
        self.quota_collection.update_one(
            {"key_id": key_id},
            {
                "$inc": {"request_count": 1},
                "$set": {"last_used": datetime.now(timezone.utc), "date": current_date}
            },
            upsert=True
        )
    
    def get_available_key(self) -> Optional[str]:
        """
        Get an API key with available quota.
        
        Returns:
            API key string if available, None if all keys exhausted
        """
        # Try current key first
        for attempt in range(len(self.keys)):
            key_info = self.keys[self.current_key_index]
            quota_data = self._get_quota_data(key_info["id"])
            
            if quota_data["request_count"] < self.daily_limit:
                # Key has available quota
                api_key = key_info["key"]
                logger.info(
                    f"✅ Using {key_info['id']} "
                    f"({quota_data['request_count'] + 1}/{self.daily_limit} requests today)"
                )
                
                # Increment usage
                self._increment_usage(key_info["id"])
                
                return api_key
            else:
                # Key exhausted, try next one
                logger.warning(
                    f"⚠️  {key_info['id']} quota exhausted "
                    f"({quota_data['request_count']}/{self.daily_limit}). "
                    f"Rotating to next key..."
                )
                self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        
        # All keys exhausted
        logger.error("❌ All API keys exhausted! All quotas used for today.")
        return None
    
    def get_quota_status(self) -> Dict:
        """
        Get overall quota status for all keys.
        
        Returns:
            Dictionary with quota information
        """
        total_used = 0
        total_available = len(self.keys) * self.daily_limit
        keys_status = []
        
        for key_info in self.keys:
            quota_data = self._get_quota_data(key_info["id"])
            used = quota_data["request_count"]
            remaining = self.daily_limit - used
            
            total_used += used
            
            keys_status.append({
                "key_id": key_info["id"],
                "used": used,
                "remaining": remaining,
                "limit": self.daily_limit,
                "status": "exhausted" if remaining == 0 else "available",
                "last_used": quota_data.get("last_used")
            })
        
        return {
            "total_keys": len(self.keys),
            "total_capacity": total_available,
            "total_used": total_used,
            "total_remaining": total_available - total_used,
            "usage_percentage": round((total_used / total_available) * 100, 1),
            "keys": keys_status,
            "reset_info": {
                "timezone": "America/Los_Angeles (Pacific Time)",
                "next_reset": "Midnight PT",
                "current_date": self._get_current_pacific_date()
            }
        }
    
    def force_reset_all_quotas(self):
        """Force reset all quota counters (for testing purposes)."""
        if self.db is None:
            logger.warning("⚠️  Cannot reset quotas: MongoDB not initialized")
            return
        
        current_date = self._get_current_pacific_date()
        result = self.quota_collection.update_many(
            {},
            {"$set": {"request_count": 0, "date": current_date}}
        )
        logger.info(f"🔄 Force reset {result.modified_count} quota counters")


# Global instance
gemini_key_manager = GeminiKeyManager()
