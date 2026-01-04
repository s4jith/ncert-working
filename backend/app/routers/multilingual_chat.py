"""
Multilingual Chat Router for NCERT AI Learning Platform

Intel-optimized: Uses OpenVINO LaBSE for cross-lingual embeddings.

Supports Indian languages:
- Hindi, Tamil, Urdu, Bengali, Marathi, Kannada, Telugu, Malayalam,
  Gujarati, Punjabi, Odia, Assamese, Sanskrit, Nepali

Students can ask questions in their native language and receive
responses in the same language.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import logging

from app.services.orchestrator_service import orchestrator_service
from app.services.openvino_multilingual_service import (
    multilingual_service, 
    SUPPORTED_LANGUAGES
)
from app.utils.performance_logger import measure_latency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Multilingual Chat"])


class MultilingualChatRequest(BaseModel):
    """Request model for multilingual chat."""
    question: str
    class_level: int = 9
    subject: str = "science"
    chapter: Optional[int] = None
    preferred_lang: Optional[str] = None  # Override detected language
    student_id: Optional[str] = None


class MultilingualChatResponse(BaseModel):
    """Response model for multilingual chat."""
    answer: str
    detected_language: str
    language_name: str
    sources_count: int
    mode: str


@router.post("/multilingual", response_model=MultilingualChatResponse)
@measure_latency("multilingual_chat")
async def multilingual_chat(request: MultilingualChatRequest):
    """
    Multilingual chat endpoint for Indian language NCERT questions.
    
    Intel-optimized: Uses OpenVINO LaBSE for cross-lingual embeddings.
    
    Supported Languages:
    - English (en), Hindi (hi), Tamil (ta), Urdu (ur), Bengali (bn)
    - Marathi (mr), Kannada (kn), Telugu (te), Malayalam (ml), Gujarati (gu)
    - Punjabi (pa), Odia (or), Assamese (as), Sanskrit (sa), Nepali (ne)
    
    The system automatically:
    1. Detects the input language
    2. Searches in language-specific namespace + English fallback
    3. Generates response in the detected language (via Gemini)
    
    Args:
        request: MultilingualChatRequest with question, class, subject
    
    Returns:
        Answer in detected language with source count
    
    Example:
        POST /api/v1/chat/multilingual
        {"question": "फोटोसिंथेसिस क्या है?", "class_level": 9, "subject": "science"}
    """
    try:
        question = request.question.strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Detect language
        if request.preferred_lang and request.preferred_lang in SUPPORTED_LANGUAGES:
            detected_lang = request.preferred_lang
            logger.info(f"🌐 Using preferred language: {detected_lang}")
        else:
            detected_lang, confidence = multilingual_service.detect_language_with_confidence(question)
            logger.info(f"🌐 Detected language: {detected_lang} (confidence: {confidence:.2f})")
        
        language_name = multilingual_service.get_language_name(detected_lang)
        
        # Determine retrieval mode based on language
        # For Indic languages, we use cross-lingual retrieval
        if multilingual_service.is_indic_language(detected_lang):
            mode = "multilingual"
            logger.info(f"   Using multilingual retrieval for {language_name}")
        else:
            mode = "basic"
        
        # Process through orchestrator with language context
        # Gemini natively handles multilingual responses
        answer, sources = orchestrator_service.answer_question(
            question=question,
            subject=request.subject,
            student_class=request.class_level,
            chapter=request.chapter,
            mode=mode
        )
        
        # Log multilingual interaction
        await _log_multilingual_interaction(
            question=question,
            answer=answer,
            language=detected_lang,
            subject=request.subject,
            student_id=request.student_id
        )
        
        return MultilingualChatResponse(
            answer=answer,
            detected_language=detected_lang,
            language_name=language_name,
            sources_count=len(sources),
            mode=mode
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Multilingual chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for multilingual chat.
    
    Returns:
        Dict with language codes and names
    """
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "default": "en",
        "indic_languages": [
            code for code in SUPPORTED_LANGUAGES.keys() 
            if code != "en"
        ],
        "auto_detection": True,
        "examples": {
            "hi": "फोटोसिंथेसिस क्या है?",
            "ta": "ஆக்ஸிஜனேஷன் என்றால் என்ன?",
            "ur": "فوٹو سنتھیسس کیا ہے؟",
            "bn": "সালোকসংশ্লেষণ কি?",
            "te": "కిరణజన్య సంయోగక్రియ అంటే ఏమిటి?",
            "kn": "ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ ಎಂದರೇನು?",
            "ml": "ഫോട്ടോസിന്തസിസ് എന്താണ്?",
            "mr": "प्रकाशसंश्लेषण म्हणजे काय?",
            "gu": "પ્રકાશસંશ્લેષણ શું છે?",
            "pa": "ਪ੍ਰਕਾਸ਼ ਸੰਸਲੇਸ਼ਣ ਕੀ ਹੈ?"
        }
    }


@router.post("/detect-language")
async def detect_language(text: str):
    """
    Detect the language of input text.
    
    Args:
        text: Input text to analyze
    
    Returns:
        Detected language code and confidence
    """
    lang, confidence = multilingual_service.detect_language_with_confidence(text)
    
    return {
        "text": text[:100] + "..." if len(text) > 100 else text,
        "language_code": lang,
        "language_name": multilingual_service.get_language_name(lang),
        "confidence": round(confidence, 2),
        "is_indic": multilingual_service.is_indic_language(lang)
    }


async def _log_multilingual_interaction(
    question: str,
    answer: str,
    language: str,
    subject: str,
    student_id: Optional[str]
):
    """Log multilingual interaction for analytics."""
    try:
        from app.db.mongo import get_database
        from datetime import datetime
        
        db = get_database()
        if db is not None:
            log_entry = {
                "type": "multilingual_chat",
                "student_id": student_id,
                "question": question,
                "answer_length": len(answer),
                "language": language,
                "subject": subject,
                "timestamp": datetime.utcnow()
            }
            db.multilingual_interactions.insert_one(log_entry)
    except Exception as e:
        logger.debug(f"Multilingual logging failed: {e}")
