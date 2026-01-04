"""
Admin Router - System management and monitoring endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
from app.services.gemini_key_manager import gemini_key_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


class QuotaStatusResponse(BaseModel):
    """Response schema for quota status."""
    total_keys: int = Field(..., description="Number of API keys configured")
    total_capacity: int = Field(..., description="Total requests available per day")
    total_used: int = Field(..., description="Requests used today")
    total_remaining: int = Field(..., description="Requests remaining today")
    usage_percentage: float = Field(..., description="Percentage of quota used")
    keys: List[Dict] = Field(..., description="Status of each API key")
    reset_info: Dict = Field(..., description="Quota reset information")


@router.get("/quota-status", response_model=QuotaStatusResponse)
async def get_quota_status():
    """
    📊 Get Gemini API quota status for all keys.
    
    Shows:
    - Total capacity across all keys
    - Current usage for each key
    - Remaining quota
    - Next reset time
    
    **Use this to monitor your API usage and avoid hitting limits!**
    """
    try:
        status = gemini_key_manager.get_quota_status()
        return status
    
    except Exception as e:
        logger.error(f"❌ Failed to get quota status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota-reset")
async def force_reset_quota():
    """
    🔄 Force reset all quota counters (for testing).
    
    **WARNING**: This should only be used for testing purposes!
    In production, quotas reset automatically at midnight Pacific Time.
    """
    try:
        gemini_key_manager.force_reset_all_quotas()
        return {
            "success": True,
            "message": "All quota counters have been reset",
            "new_status": gemini_key_manager.get_quota_status()
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to reset quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    💚 System health check.
    
    Returns:
    - API status
    - Quota availability
    - System readiness
    """
    try:
        quota_status = gemini_key_manager.get_quota_status()
        
        # Check if any keys are available
        has_available_keys = quota_status["total_remaining"] > 0
        
        return {
            "status": "healthy" if has_available_keys else "quota_exhausted",
            "api_keys_configured": quota_status["total_keys"],
            "requests_remaining": quota_status["total_remaining"],
            "quota_percentage_used": quota_status["usage_percentage"],
            "ready": has_available_keys
        }
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "ready": False
        }
