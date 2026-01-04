"""
Voice Chat Router for NCERT AI Learning Platform

Intel-optimized: Voice support at interface level; core RAG and Intel optimization remain same.

Provides voice-to-text chat endpoint that accepts audio input and processes through
the existing RAG pipeline after speech-to-text conversion.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import logging
import io
from datetime import datetime

from app.services.orchestrator_service import orchestrator_service
from app.utils.performance_logger import measure_latency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Voice Chat"])


@router.post("/voice")
@measure_latency("voice_chat")
async def voice_chat(
    audio: UploadFile = File(...),
    student_class: int = Form(6),
    subject: str = Form("Mathematics"),
    chapter: Optional[int] = Form(None),
    student_id: Optional[str] = Form(None)
):
    """
    Voice-based chat endpoint.
    
    Intel-optimized: Voice support at interface level. Core RAG pipeline and
    Intel OpenVINO optimizations remain unchanged.
    
    This endpoint:
    1. Accepts audio file (WAV, MP3, WebM)
    2. Converts speech-to-text (via external STT or browser Web Speech API)
    3. Processes through existing text RAG pipeline
    4. Returns text response (can be converted to speech on frontend)
    
    Args:
        audio: Audio file upload
        student_class: Student's class level (5-12)
        subject: Subject name
        chapter: Optional chapter number
        student_id: Optional student ID for logging
    
    Returns:
        Dict with transcription and RAG answer
    """
    try:
        logger.info(f"🎤 Voice chat request: Class {student_class} {subject}")
        logger.info(f"   Audio: {audio.filename}, {audio.content_type}")
        
        # Read audio file
        audio_content = await audio.read()
        audio_size_kb = len(audio_content) / 1024
        logger.info(f"   Audio size: {audio_size_kb:.2f} KB")
        
        # Speech-to-text conversion
        # Note: In production, integrate with:
        # - Intel OpenVINO speech recognition models
        # - Google Speech-to-Text API
        # - Azure Speech Services
        # - Browser Web Speech API (client-side)
        transcription = await _transcribe_audio(audio_content, audio.content_type)
        
        if not transcription or len(transcription.strip()) < 3:
            return {
                "success": False,
                "error": "Could not transcribe audio. Please try again or use text input.",
                "transcription": "",
                "answer": ""
            }
        
        logger.info(f"   Transcription: {transcription[:100]}...")
        
        # Process through existing RAG pipeline
        answer, sources = orchestrator_service.answer_question(
            question=transcription,
            subject=subject,
            student_class=student_class,
            chapter=chapter,
            mode="quick"  # Voice typically expects quick responses
        )
        
        # Log voice interaction
        await _log_voice_interaction(
            student_id=student_id,
            transcription=transcription,
            answer=answer,
            subject=subject,
            student_class=student_class
        )
        
        return {
            "success": True,
            "transcription": transcription,
            "answer": answer,
            "sources_count": len(sources),
            "mode": "voice"
        }
        
    except Exception as e:
        logger.error(f"❌ Voice chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _transcribe_audio(audio_content: bytes, content_type: str) -> str:
    """
    Transcribe audio to text.
    
    Note: This is a placeholder implementation. In production:
    - Use Intel OpenVINO speech models for on-device processing
    - Or integrate with cloud STT services (Google, Azure)
    - Or rely on browser Web Speech API (client-side)
    
    For Intel Unnati demo, voice is supported at interface level.
    """
    # Placeholder: Return instruction for demo
    # In production, integrate actual STT here
    
    # Check file size - if too small, likely not valid audio
    if len(audio_content) < 1000:
        return ""
    
    # For demo purposes, return a sample response indicating voice was received
    # In production, this would call actual STT service
    logger.info("   Note: Using placeholder STT. Integrate real STT for production.")
    
    # Return placeholder indicating voice support is ready
    # Frontend should use Web Speech API for actual transcription
    return "[Voice input received - integrate STT service or use browser Web Speech API for transcription]"


async def _log_voice_interaction(
    student_id: Optional[str],
    transcription: str,
    answer: str,
    subject: str,
    student_class: int
):
    """Log voice interaction for analytics."""
    try:
        from app.db.mongo import get_database
        db = get_database()
        
        if db is not None:
            log_entry = {
                "type": "voice_chat",
                "student_id": student_id,
                "transcription": transcription,
                "answer_length": len(answer),
                "subject": subject,
                "class": student_class,
                "timestamp": datetime.utcnow()
            }
            db.voice_interactions.insert_one(log_entry)
    except Exception as e:
        logger.debug(f"Voice logging failed: {e}")


@router.get("/voice/status")
async def voice_status():
    """Get voice chat service status."""
    return {
        "available": True,
        "stt_backend": "placeholder",
        "note": "Voice supported at interface level. Use browser Web Speech API for transcription, or integrate production STT.",
        "supported_formats": ["audio/wav", "audio/mp3", "audio/webm", "audio/ogg"]
    }
