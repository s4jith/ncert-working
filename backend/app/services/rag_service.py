"""
RAG Service - OPEA-compliant RAG Pipeline
Core service for retrieval-augmented generation
"""

import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.config import settings
from app.db.pinecone import query_vectors
from app.db.mongodb import get_cached_response, set_cached_response, get_conversation_context
from app.db.models import ChatSource, SourceType, LLMProvider

logger = logging.getLogger(__name__)


class RAGService:
    """OPEA-compliant RAG Service for NCERT Q&A"""
    
    def __init__(self):
        self.min_relevance_score = settings.RAG_MIN_RELEVANCE_SCORE
        self.top_k = settings.RAG_TOP_K
        self.rerank_top_k = settings.RAG_RERANK_TOP_K
    
    async def process_query(
        self,
        query: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        language: str = "en",
        conversation_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Tuple[str, List[Dict], bool]:
        """
        Process a query through the RAG pipeline
        
        Returns:
            Tuple of (context_text, sources, is_in_scope)
        """
        start_time = datetime.utcnow()
        
        # 1. Check cache first
        if use_cache:
            question_hash = self._hash_question(query, grade, subject)
            cached = await get_cached_response(question_hash)
            if cached:
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached["answer"], cached["sources"], True
        
        # 2. Detect language (simplified - would use proper detection in production)
        detected_language = self._detect_language(query)
        
        # 3. Retrieve relevant documents from Pinecone
        results = await query_vectors(
            query_text=query,
            class_num=str(grade) if grade else None,
            subject=subject,
            top_k=self.top_k
        )
        
        # 4. Filter by relevance score
        relevant_results = [
            r for r in results 
            if r["score"] >= self.min_relevance_score
        ]
        
        # 5. Check if query is in-scope
        if not relevant_results:
            return self._get_out_of_scope_response(detected_language), [], False
        
        # 6. Format sources for citations
        sources = self._format_sources(relevant_results)
        
        # 7. Build context from retrieved documents
        context = self._build_context(relevant_results)
        
        # 8. Get conversation history for context
        conversation_context = ""
        if conversation_id:
            history = await get_conversation_context(conversation_id, limit=3)
            if history:
                conversation_context = self._format_conversation_history(history)
        
        elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.info(f"RAG retrieval completed in {elapsed_ms}ms, found {len(relevant_results)} relevant docs")
        
        return context, sources, True
    
    def _hash_question(self, query: str, grade: Optional[int], subject: Optional[str]) -> str:
        """Create hash for caching"""
        key = f"{query.lower().strip()}|{grade or 'any'}|{subject or 'any'}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection (Hindi/English/Urdu)"""
        # Check for Devanagari script (Hindi)
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        # Check for Arabic script (Urdu)
        urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        total = len(text)
        if total == 0:
            return "en"
        
        if hindi_chars / total > 0.3:
            return "hi"
        if urdu_chars / total > 0.3:
            return "ur"
        
        return "en"
    
    def _get_out_of_scope_response(self, language: str) -> str:
        """Return appropriate 'I don't know' response"""
        responses = {
            "en": "I don't have enough information in my NCERT knowledge base to answer this question accurately. Please try asking about topics covered in NCERT textbooks for grades 5-12.",
            "hi": "मेरे पास इस प्रश्न का सटीक उत्तर देने के लिए NCERT पाठ्यपुस्तकों में पर्याप्त जानकारी नहीं है। कृपया कक्षा 5-12 की NCERT पुस्तकों में शामिल विषयों के बारे में पूछें।",
            "ur": "میرے پاس اس سوال کا درست جواب دینے کے لیے NCERT نصابی کتابوں میں کافی معلومات نہیں ہیں۔ براہ کرم جماعت 5-12 کی NCERT کتابوں میں شامل موضوعات کے بارے میں پوچھیں۔"
        }
        return responses.get(language, responses["en"])
    
    def _format_sources(self, results: List[Dict]) -> List[Dict]:
        """Format retrieved documents as sources for citations"""
        sources = []
        for result in results:
            source = {
                "type": SourceType.NCERT_TEXTBOOK,
                "name": f"{result.get('subject', 'Unknown')} - {result.get('chapter', 'Unknown')}",
                "class": f"Class {result.get('class_num', 'Unknown')}",
                "subject": result.get("subject"),
                "chapter": result.get("chapter"),
                "page": result.get("page"),
                "relevance": f"{int(result.get('score', 0) * 100)}%"
            }
            sources.append(source)
        return sources
    
    def _build_context(self, results: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for i, result in enumerate(results[:self.rerank_top_k], 1):
            source_info = f"[Source {i}: Class {result.get('class_num', 'N/A')}, {result.get('subject', 'N/A')}, {result.get('chapter', 'N/A')}]"
            text = result.get("text", "")
            context_parts.append(f"{source_info}\n{text}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for context"""
        formatted = []
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("question") or msg.get("answer", "")
            formatted.append(f"{role}: {content[:500]}")
        return "\n".join(formatted)
    
    def build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: str = "",
        language: str = "en"
    ) -> str:
        """Build the final prompt for LLM - optimized for STEM subjects"""
        
        prompt = f"""You are an expert NCERT tutor specializing in helping students from grades 5-12 with Mathematics, Physics, Chemistry, Biology, and other subjects.

IMPORTANT GUIDELINES FOR STEM SUBJECTS:
- For MATH problems: Show step-by-step solutions, write formulas clearly, explain each step
- For PHYSICS: State relevant formulas, units, and show calculations
- For CHEMISTRY: Include chemical equations, molecular formulas, and reaction mechanisms
- For BIOLOGY: Use proper scientific terminology and diagrams descriptions

CONTEXT FROM NCERT TEXTBOOKS:
{context}

{f'PREVIOUS CONVERSATION:{chr(10)}{conversation_history}{chr(10)}{chr(10)}' if conversation_history else ''}STUDENT QUESTION:
{query}

INSTRUCTIONS:
1. Answer ONLY based on the NCERT content provided above
2. For formulas and equations, write them clearly (e.g., E = mc², H₂O, F = ma)
3. Show step-by-step solutions for numerical problems
4. Use simple language appropriate for students
5. Cite your sources using [Source 1], [Source 2], etc.
6. If the question involves calculations, show the complete working
7. If information is not in the context, say "This topic is not covered in the provided NCERT content"

YOUR DETAILED ANSWER:"""
        
        return prompt


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get RAG service singleton"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
