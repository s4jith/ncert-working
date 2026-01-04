"""
Authentication Router
- Login with user_id and password
- Password change for first-time login
- Session management
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime
from app.db.mongo import db
import hashlib
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# === Pydantic Models ===

class LoginRequest(BaseModel):
    user_id: str
    password: str
    role: str


class PasswordChangeRequest(BaseModel):
    user_id: str
    old_password: str
    new_password: str


# === Helper Functions ===

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password


# === Authentication Endpoints ===

@router.post("/login")
async def login(request: LoginRequest):
    """
    Login with user_id and password
    Returns user data and session token
    """
    try:
        # Find user by user_id and role
        user = db.users.find_one({
            "user_id": request.user_id,
            "role": request.role
        })
        
        if not user:
            return {
                "success": False,
                "error": f"No {request.role} found with this user ID"
            }
        
        # Verify password
        if not verify_password(request.password, user.get("password", "")):
            return {
                "success": False,
                "error": "Invalid password"
            }
        
        # Check if account is active
        if not user.get("is_active", True):
            return {
                "success": False,
                "error": "Account is deactivated. Please contact admin."
            }
        
        # Check if this is first login (password is default pattern)
        default_password = f"{request.user_id}@123"
        is_first_login = request.password == default_password
        
        # Update last login time
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Return user data
        return {
            "success": True,
            "first_login": is_first_login,
            "user_id": user["user_id"],
            "session_id": session_id,
            "user": {
                "id": str(user["_id"]),
                "user_id": user["user_id"],
                "name": user.get("name", "User"),
                "email": user.get("email", ""),
                "role": user["role"],
                "class_level": user.get("class_level"),
                "is_onboarded": user.get("isOnboarded", False)
            }
        }
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return {
            "success": False,
            "error": "Login failed. Please try again."
        }


@router.post("/change-password")
async def change_password(request: PasswordChangeRequest):
    """
    Change user password (for first-time login or password reset)
    """
    try:
        # Find user
        user = db.users.find_one({"user_id": request.user_id})
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Verify old password
        if not verify_password(request.old_password, user.get("password", "")):
            return {
                "success": False,
                "error": "Current password is incorrect"
            }
        
        # Validate new password
        if len(request.new_password) < 8:
            return {
                "success": False,
                "error": "New password must be at least 8 characters"
            }
        
        # Hash and update password
        new_hashed = hash_password(request.new_password)
        
        db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password": new_hashed,
                    "password_changed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }
    
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return {
            "success": False,
            "error": "Failed to change password"
        }


@router.post("/complete-onboarding")
async def complete_onboarding(data: dict = Body(...)):
    """
    Complete student onboarding and save profile data to MongoDB
    This marks the student as onboarded so they go directly to dashboard on next login
    """
    try:
        user_id = data.get("user_id")
        
        if not user_id:
            return {
                "success": False,
                "error": "User ID is required"
            }
        
        # Find user
        user = db.users.find_one({"user_id": user_id})
        
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Prepare update data
        update_data = {
            "isOnboarded": True,
            "onboarded_at": datetime.utcnow()
        }
        
        # Save optional onboarding data if provided
        if data.get("profile"):
            profile = data["profile"]
            if profile.get("name"):
                update_data["name"] = profile["name"]
            if profile.get("classLevel"):
                update_data["class_level"] = profile["classLevel"]
        
        if data.get("avatar"):
            avatar = data["avatar"]
            if avatar.get("seed"):
                update_data["avatar_seed"] = avatar["seed"]
            if avatar.get("style"):
                update_data["avatar_style"] = avatar["style"]
            if avatar.get("username"):
                update_data["display_username"] = avatar["username"]
        
        if data.get("academics"):
            update_data["previous_academics"] = data["academics"]
        
        if data.get("calendar"):
            update_data["exam_calendar"] = data["calendar"]
        
        # Update user in database
        result = db.users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data}
        )
        
        if result.modified_count > 0 or result.matched_count > 0:
            logger.info(f"Onboarding completed for user: {user_id}")
            return {
                "success": True,
                "message": "Onboarding completed successfully"
            }
        else:
            return {
                "success": False,
                "error": "Failed to update user"
            }
        
    except Exception as e:
        logger.error(f"Complete onboarding error: {e}")
        return {
            "success": False,
            "error": "Failed to complete onboarding"
        }


@router.post("/signup")
async def signup(user_data: dict = Body(...)):
    """
    Student signup - DISABLED (admin creates students only)
    This endpoint returns an error message
    """
    return {
        "success": False,
        "error": "Student registration is disabled. Please contact your admin to create an account."
    }
