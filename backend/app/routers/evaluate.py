"""
Evaluate Router - MCQ evaluation endpoints.
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import EvaluationRequest, EvaluationResponse
from app.services.eval_service import eval_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/evaluate",
    tags=["Evaluation"]
)


@router.post("/", response_model=EvaluationResponse)
async def evaluate_mcqs(request: EvaluationRequest):
    """
    Evaluate student's MCQ answers.
    
    Compares student's selected answers with correct answers,
    calculates score and percentage, generates feedback,
    and saves results to MongoDB Atlas.
    
    **Returns:**
    - Total questions and correct answers
    - Percentage score
    - Personalized feedback
    - Per-question breakdown
    - MongoDB document ID
    """
    try:
        logger.info(f"Evaluation request: Student {request.student_id}, Class {request.class_level}, {request.subject}, Ch. {request.chapter}")
        
        # Evaluate answers
        result, evaluation_id = await eval_service.evaluate_mcqs(
            student_id=request.student_id or "anonymous",
            class_level=request.class_level,
            subject=request.subject,
            chapter=request.chapter,
            mcqs=request.mcqs,
            answers=request.answers
        )
        
        return EvaluationResponse(
            result=result,
            saved_to_db=True,
            evaluation_id=evaluation_id
        )
    
    except Exception as e:
        logger.error(f"❌ Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
