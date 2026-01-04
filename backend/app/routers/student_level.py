"""
Student Level Router for Adaptive Explanations

Implements adaptive explanation mode based on student proficiency level.
Maps student level to explanation mode:
- beginner → simple mode
- intermediate → quick mode  
- advanced → deepdive mode
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/student", tags=["Student Profile"])


class StudentLevel(BaseModel):
    """Student proficiency level model."""
    level: Literal["beginner", "intermediate", "advanced"]


class StudentLevelResponse(BaseModel):
    """Response with student level and mapped mode."""
    student_id: str
    level: str
    explanation_mode: str
    updated_at: Optional[str] = None


# Level to mode mapping for adaptive explanations
LEVEL_TO_MODE = {
    "beginner": "simple",
    "intermediate": "quick",
    "advanced": "deepdive"
}


@router.get("/level/{student_id}")
async def get_student_level(student_id: str) -> StudentLevelResponse:
    """
    Get student's proficiency level and corresponding explanation mode.
    
    Adaptive explanations stretch goal:
    - beginner students get simple, step-by-step explanations
    - intermediate students get quick, focused answers
    - advanced students get comprehensive deepdive explanations
    
    Args:
        student_id: Student's unique identifier
    
    Returns:
        Student level and mapped explanation mode
    """
    try:
        from app.db.mongo import get_database
        db = get_database()
        
        if db is None:
            # Default to intermediate if DB unavailable
            return StudentLevelResponse(
                student_id=student_id,
                level="intermediate",
                explanation_mode="quick"
            )
        
        # Look up student level
        student = db.students.find_one({"_id": student_id})
        
        if student and "level" in student:
            level = student["level"]
            mode = LEVEL_TO_MODE.get(level, "quick")
            updated_at = student.get("level_updated_at")
            
            return StudentLevelResponse(
                student_id=student_id,
                level=level,
                explanation_mode=mode,
                updated_at=str(updated_at) if updated_at else None
            )
        
        # Default for new students
        return StudentLevelResponse(
            student_id=student_id,
            level="intermediate",
            explanation_mode="quick"
        )
        
    except Exception as e:
        logger.error(f"Failed to get student level: {e}")
        return StudentLevelResponse(
            student_id=student_id,
            level="intermediate",
            explanation_mode="quick"
        )


@router.put("/level/{student_id}")
async def update_student_level(student_id: str, level_data: StudentLevel) -> StudentLevelResponse:
    """
    Update student's proficiency level.
    
    This enables adaptive explanations based on student profile.
    The system automatically adjusts explanation complexity.
    
    Args:
        student_id: Student's unique identifier
        level_data: New level (beginner/intermediate/advanced)
    
    Returns:
        Updated student level and explanation mode
    """
    try:
        from app.db.mongo import get_database
        db = get_database()
        
        level = level_data.level
        mode = LEVEL_TO_MODE.get(level, "quick")
        
        if db is not None:
            # Update student level in database
            db.students.update_one(
                {"_id": student_id},
                {
                    "$set": {
                        "level": level,
                        "level_updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Updated student {student_id} level to {level} (mode: {mode})")
        
        return StudentLevelResponse(
            student_id=student_id,
            level=level,
            explanation_mode=mode,
            updated_at=str(datetime.utcnow())
        )
        
    except Exception as e:
        logger.error(f"Failed to update student level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/level/mode-mapping")
async def get_mode_mapping():
    """Get the level to explanation mode mapping."""
    return {
        "mapping": LEVEL_TO_MODE,
        "description": {
            "beginner": "Simple, step-by-step explanations with examples",
            "intermediate": "Quick, focused answers suitable for regular students",
            "advanced": "Comprehensive deepdive from fundamentals with web resources"
        }
    }
