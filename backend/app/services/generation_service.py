"""
OPEA-style Generation Service

Intel-optimized: Uses Gemini for high-quality answer generation.

This service wraps the answer generation logic following OPEA architecture:
- Context-aware prompt construction
- Multi-source answer synthesis
- Educational content formatting

Maps to OPEA's "Generation Microservice" in the Enterprise RAG reference.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from app.utils.performance_logger import measure_latency, IntelOptimizedConfig
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig(IntelOptimizedConfig):
    """Configuration for Generation Service."""
    intel_optimized: bool = True
    component_name: str = "GenerationService"
    description: str = "OPEA-style generation: LLM answer synthesis from retrieved context"
    
    # Generation settings
    model: str = "gemini-2.0-flash"
    max_textbook_chunks: int = 10
    max_llm_chunks: int = 2
    max_web_chunks: int = 5


class GenerationService:
    """
    OPEA-style Generation Service for answer synthesis.
    
    Intel-optimized: Efficient prompt construction and response generation.
    
    Modes:
        - Basic: Quick, focused answers
        - DeepDive: Comprehensive explanations from fundamentals
    
    This component maps to OPEA's "Generation Microservice" pattern.
    """
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        self.config = config or GenerationConfig()
        self.gemini = gemini_service
        
        logger.info(f"✅ {self.config.component_name} initialized (Intel-optimized: {self.config.intel_optimized})")
    
    @measure_latency("rag_generation")
    def generate_answer(
        self,
        question: str,
        textbook_chunks: List[Dict],
        llm_chunks: List[Dict],
        web_chunks: List[Dict],
        class_distribution: Dict[int, int],
        student_class: int,
        subject: str,
        mode: str = "basic"
    ) -> str:
        """
        Generate answer from retrieved context.
        
        Intel-optimized: Efficient multi-source context synthesis.
        
        Args:
            question: Student's question
            textbook_chunks: Retrieved textbook content
            llm_chunks: Cached LLM answers
            web_chunks: Web content
            class_distribution: Chunks per class level
            student_class: Student's class level
            subject: Subject name
            mode: "basic" or "deepdive"
        
        Returns:
            Generated answer string
        """
        # Handle no-content fallback
        if not textbook_chunks and not llm_chunks and not web_chunks:
            return self._generate_fallback_answer(question, student_class, subject)
        
        # Build context from all sources
        context = self._build_context(textbook_chunks, llm_chunks, web_chunks)
        
        # Generate prompt based on mode
        prompt = self._build_prompt(question, context, student_class, subject, mode)
        
        # Generate answer
        answer = self.gemini.generate_response(prompt)
        
        logger.info(f"✅ [{self.config.component_name}] Generated answer ({len(answer)} chars)")
        
        return answer
    
    def _build_context(
        self,
        textbook_chunks: List[Dict],
        llm_chunks: List[Dict],
        web_chunks: List[Dict]
    ) -> str:
        """Build combined context from all sources."""
        sections = []
        
        # Priority 1: Textbook content
        if textbook_chunks:
            tb_content = []
            for chunk in textbook_chunks[:self.config.max_textbook_chunks]:
                class_level = chunk.get('class', '')
                tb_content.append(f"[Class {class_level}] {chunk['text']}")
            sections.append("**PRIMARY SOURCE - NCERT Textbook:**\n" + "\n\n".join(tb_content))
        
        # Priority 2: LLM cached answers
        if llm_chunks:
            llm_content = []
            for chunk in llm_chunks[:self.config.max_llm_chunks]:
                topic = chunk.get('topic', 'general')
                llm_content.append(f"[Topic: {topic}] {chunk['text']}")
            sections.append("**REFERENCE - Previous Explanations:**\n" + "\n\n".join(llm_content))
        
        # Priority 3: Web content
        if web_chunks:
            web_content = []
            for chunk in web_chunks[:self.config.max_web_chunks]:
                url = chunk.get('url', 'N/A')[:50]
                web_content.append(f"[Source: {url}...] {chunk['text']}")
            sections.append("**SUPPLEMENTARY - Web Resources:**\n" + "\n\n".join(web_content))
        
        return "\n\n".join(sections)
    
    def _build_prompt(
        self,
        question: str,
        context: str,
        student_class: int,
        subject: str,
        mode: str
    ) -> str:
        """Build generation prompt."""
        mode_desc = "COMPREHENSIVE" if mode == "deepdive" else "FOCUSED"
        
        return f"""You are an expert NCERT tutor for Class {student_class} {subject} providing a {mode_desc} explanation.

**STUDENT QUESTION:** {question}

**AVAILABLE SOURCES:**
{context}

**INSTRUCTIONS:**
1. Base your answer on NCERT textbook content (if available)
2. Use previous explanations for clarity
3. Add web resources for examples
4. NO HALLUCINATION - only use provided sources
5. {'Start from fundamentals' if mode == 'deepdive' else 'Be direct and concise'}
6. Use headings, bullet points, and examples
7. Appropriate for Class {student_class} students

Generate a {'comprehensive' if mode == 'deepdive' else 'clear and focused'} answer:"""
    
    def _generate_fallback_answer(self, question: str, student_class: int, subject: str) -> str:
        """Generate fallback answer using general knowledge."""
        logger.info(f"⚠️ [{self.config.component_name}] No RAG content, using fallback")
        
        prompt = f"""You are an expert tutor for Class {student_class} {subject}.
The student asked: "{question}"

I could not find specific textbook content. Please answer using general knowledge,
but mention that this is based on general principles, not the specific NCERT textbook.
Keep the explanation simple and suitable for a Class {student_class} student."""
        
        return self.gemini.generate_response(prompt)
    
    @measure_latency("mcq_generation")
    def generate_mcq(self, context: str, topic: str, difficulty: str = "medium") -> Dict:
        """
        Generate MCQ question from context.
        
        Intel-optimized: Can fall back to OpenVINO MCQ service for local generation.
        
        Args:
            context: Source content for question
            topic: Topic name
            difficulty: easy/medium/hard
        
        Returns:
            MCQ dict with question, options, correct_answer
        """
        prompt = f"""Generate a {difficulty} difficulty MCQ for topic: {topic}

Context: {context[:1000]}

Return JSON format:
{{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], "correct_answer": "A"}}"""
        
        response = self.gemini.generate_response(prompt)
        
        # Parse JSON response (simplified)
        import json
        try:
            return json.loads(response)
        except:
            return {"question": response, "options": [], "correct_answer": ""}
    
    def get_status(self) -> Dict:
        """Get service status for Intel endpoint."""
        return {
            "service": self.config.component_name,
            "intel_optimized": self.config.intel_optimized,
            "model": self.config.model,
            "modes": ["basic", "deepdive"]
        }


# Singleton instance
generation_service = GenerationService()
