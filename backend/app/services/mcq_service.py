"""
MCQ Service - Handles MCQ generation and management.

Supports hybrid pipeline:
- Gemini (default): Cloud-based, high quality
- OpenVINO (local): Intel-accelerated, fast, on-device
"""

from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.models.schemas import MCQ
import logging
import time
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Lazy import for OpenVINO MCQ service
_openvino_mcq_service = None


def get_openvino_mcq_service():
    """Lazy load OpenVINO MCQ service."""
    global _openvino_mcq_service
    if _openvino_mcq_service is None:
        try:
            from app.services.openvino_mcq_service import get_openvino_mcq_service as get_ov_service
            _openvino_mcq_service = get_ov_service()
        except Exception as e:
            logger.warning(f"OpenVINO MCQ service unavailable: {e}")
            _openvino_mcq_service = None
    return _openvino_mcq_service


class MCQService:
    """
    Service for generating and managing MCQs.
    
    Supports hybrid pipeline:
    - use_local_model=False (default): Uses Gemini for high-quality MCQs
    - use_local_model=True: Uses Intel OpenVINO for fast local generation
    """
    
    def __init__(self):
        self.gemini = gemini_service
        self.rag = rag_service
    
    def generate_mcqs(
        self,
        class_level: int,
        subject: str,
        chapter: int,
        num_questions: int = 5,
        page_range: tuple[int, int] = None,
        use_local_model: bool = False
    ) -> Tuple[List[MCQ], str, Optional[float]]:
        """
        Generate MCQs using RAG context and AI.
        
        Args:
            class_level: Class (5-12)
            subject: Subject name
            chapter: Chapter number
            num_questions: Number of MCQs to generate
            page_range: Optional (start_page, end_page)
            use_local_model: Use Intel OpenVINO local model
        
        Returns:
            Tuple of (List of MCQ objects, pipeline_used, inference_time_ms)
        """
        try:
            # Step 1: Retrieve chapter context from Pinecone
            logger.info(f"Retrieving context for Class {class_level}, {subject}, Chapter {chapter}")
            context = self.rag.retrieve_chapter_context(
                class_level=class_level,
                subject=subject,
                chapter=chapter
            )
            
            # Step 2: Choose generation pipeline
            if use_local_model:
                return self._generate_with_openvino(
                    context=context,
                    num_questions=num_questions,
                    class_level=class_level,
                    subject=subject,
                    chapter=chapter
                )
            else:
                return self._generate_with_gemini(
                    context=context,
                    num_questions=num_questions,
                    class_level=class_level,
                    subject=subject,
                    chapter=chapter
                )
        
        except Exception as e:
            logger.error(f"❌ MCQ generation failed: {e}")
            raise
    
    def _generate_with_gemini(
        self,
        context: str,
        num_questions: int,
        class_level: int,
        subject: str,
        chapter: int
    ) -> Tuple[List[MCQ], str, Optional[float]]:
        """Generate MCQs using Gemini (cloud)."""
        logger.info(f"Generating {num_questions} MCQs with Gemini...")
        
        start_time = time.perf_counter()
        
        mcq_dicts = self.gemini.generate_mcqs(
            context=context,
            num_questions=num_questions,
            class_level=class_level,
            subject=subject,
            chapter=chapter
        )
        
        inference_time_ms = (time.perf_counter() - start_time) * 1000
        
        # Convert to Pydantic models
        mcqs = [MCQ(**mcq) for mcq in mcq_dicts]
        
        logger.info(f"✅ Generated {len(mcqs)} MCQs with Gemini in {inference_time_ms:.1f}ms")
        return mcqs, "gemini", inference_time_ms
    
    def _generate_with_openvino(
        self,
        context: str,
        num_questions: int,
        class_level: int,
        subject: str,
        chapter: int
    ) -> Tuple[List[MCQ], str, Optional[float]]:
        """Generate MCQs using Intel OpenVINO (local)."""
        logger.info(f"Generating {num_questions} MCQs with OpenVINO (Intel)...")
        
        ov_service = get_openvino_mcq_service()
        
        if ov_service is None or not ov_service.is_available():
            logger.warning("⚠️ OpenVINO MCQ service unavailable, falling back to Gemini")
            mcqs, _, time_ms = self._generate_with_gemini(
                context, num_questions, class_level, subject, chapter
            )
            return mcqs, "gemini-fallback", time_ms
        
        try:
            # Generate with OpenVINO
            mcq_dicts, inference_time_ms = ov_service.generate_mcq_draft(
                text_chunk=context,
                num_questions=num_questions
            )
            
            # Convert to Pydantic models
            mcqs = [MCQ(**mcq) for mcq in mcq_dicts]
            
            if len(mcqs) < num_questions:
                logger.warning(f"OpenVINO generated only {len(mcqs)}/{num_questions} MCQs")
            
            logger.info(f"✅ Generated {len(mcqs)} MCQs with OpenVINO in {inference_time_ms:.1f}ms")
            return mcqs, "openvino", inference_time_ms
            
        except Exception as e:
            logger.error(f"OpenVINO generation failed: {e}, falling back to Gemini")
            mcqs, _, time_ms = self._generate_with_gemini(
                context, num_questions, class_level, subject, chapter
            )
            return mcqs, "gemini-fallback", time_ms
    
    def get_openvino_status(self) -> dict:
        """Get OpenVINO MCQ service status."""
        ov_service = get_openvino_mcq_service()
        if ov_service is None:
            return {"available": False, "error": "Service not initialized"}
        return ov_service.get_status()


# Global MCQ service instance
mcq_service = MCQService()

