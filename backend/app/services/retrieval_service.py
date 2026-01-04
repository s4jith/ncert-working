"""
OPEA-style Retrieval Service

Intel-optimized: Uses Gemini embeddings for semantic search across multiple indices.

This service wraps the multi-index retrieval logic following OPEA architecture:
- Query embedding generation
- Multi-class Pinecone search
- Web content retrieval
- LLM-generated content retrieval

Maps to OPEA's "Retrieval Microservice" in the Enterprise RAG reference.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from app.utils.performance_logger import measure_latency, IntelOptimizedConfig
from app.db.mongo import pinecone_db, pinecone_web_db, pinecone_llm_db
from app.services.gemini_key_manager import gemini_key_manager
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig(IntelOptimizedConfig):
    """Configuration for Retrieval Service."""
    intel_optimized: bool = True
    component_name: str = "RetrievalService"
    description: str = "OPEA-style retrieval: Multi-index semantic search"
    
    # Retrieval settings
    embedding_model: str = "models/text-embedding-004"
    chunks_per_class: int = 5
    web_top_k: int = 10
    llm_top_k: int = 3
    llm_similarity_threshold: float = 0.75


class RetrievalService:
    """
    OPEA-style Retrieval Service for semantic search across multiple indices.
    
    Intel-optimized: Uses efficient embedding generation and parallel index queries.
    
    Indices:
        1. Textbook Index (ncert-all-subjects) - Primary source
        2. Web Content Index (ncert-web-content) - Supplementary
        3. LLM Generated Index (ncert-llm) - Cached answers
    
    This component maps to OPEA's "Retrieval Microservice" pattern.
    """
    
    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        
        # Pinecone indices
        self.textbook_db = pinecone_db
        self.web_db = pinecone_web_db
        self.llm_db = pinecone_llm_db
        
        # Subject configurations
        self.subject_namespaces = {
            "Mathematics": "mathematics",
            "Physics": "physics",
            "Chemistry": "chemistry",
            "Biology": "biology",
            "Social Science": "social_science",
            "History": "history",
            "Geography": "geography",
            "Civics": "civics",
            "Economics": "economics",
            "English": "english",
            "Hindi": "hindi"
        }
        
        self.subject_class_ranges = {
            "Mathematics": list(range(5, 13)),
            "Physics": list(range(11, 13)),
            "Chemistry": list(range(11, 13)),
            "Biology": list(range(11, 13)),
            "Social Science": list(range(5, 11)),
            "History": list(range(5, 13)),
            "Geography": list(range(5, 13)),
            "Civics": list(range(5, 11)),
            "Economics": list(range(9, 13)),
            "English": list(range(5, 13)),
            "Hindi": list(range(5, 13))
        }
        
        logger.info(f"✅ {self.config.component_name} initialized (Intel-optimized: {self.config.intel_optimized})")
    
    @measure_latency("embedding_generation")
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Gemini text-embedding-004.
        
        Args:
            text: Input text to embed
        
        Returns:
            768-dimensional embedding vector
        """
        api_key = gemini_key_manager.get_available_key()
        genai.configure(api_key=api_key)
        
        result = genai.embed_content(
            model=self.config.embedding_model,
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    
    def get_namespace(self, subject: str) -> str:
        """Get Pinecone namespace for subject."""
        return self.subject_namespaces.get(subject, subject.lower().replace(" ", "_"))
    
    def get_prerequisite_classes(self, subject: str, student_class: int, mode: str = "basic") -> List[int]:
        """Get list of classes to search based on mode."""
        available_classes = self.subject_class_ranges.get(subject, list(range(5, 13)))
        available_classes = [c for c in available_classes if c <= student_class]
        
        if mode == "basic":
            prerequisite_range = 2
            start_class = max(available_classes[0] if available_classes else 5, student_class - prerequisite_range)
            return [c for c in available_classes if start_class <= c <= student_class]
        else:
            return available_classes
    
    @measure_latency("rag_retrieval")
    def retrieve(
        self,
        query_text: str,
        subject: str,
        student_class: int,
        chapter: Optional[int] = None,
        mode: str = "basic"
    ) -> Dict:
        """
        Retrieve relevant content from all indices.
        
        Intel-optimized: Single embedding generation, parallel index queries.
        
        Args:
            query_text: Student's question
            subject: Subject name
            student_class: Current class level
            chapter: Optional chapter filter
            mode: "basic" or "deepdive"
        
        Returns:
            Dict with textbook_chunks, llm_chunks, web_chunks, class_distribution, query_embedding
        """
        logger.info(f"🔍 [{self.config.component_name}] Retrieving for: {query_text[:50]}...")
        
        # Generate embedding ONCE (optimized)
        query_embedding = self.generate_embedding(query_text)
        
        # Query all indices with shared embedding
        textbook_chunks, class_dist = self.query_textbook(
            query_embedding, subject, student_class, chapter, mode
        )
        
        llm_chunks = self.query_llm_cache(query_embedding, subject)
        
        web_chunks = []
        if mode == "deepdive":
            web_chunks = self.query_web_content(query_embedding, subject, student_class)
        
        logger.info(f"📊 [{self.config.component_name}] Retrieved: Textbook={len(textbook_chunks)}, LLM={len(llm_chunks)}, Web={len(web_chunks)}")
        
        return {
            "textbook_chunks": textbook_chunks,
            "llm_chunks": llm_chunks,
            "web_chunks": web_chunks,
            "class_distribution": class_dist,
            "query_embedding": query_embedding
        }
    
    def query_textbook(
        self,
        query_embedding: List[float],
        subject: str,
        student_class: int,
        chapter: Optional[int] = None,
        mode: str = "basic"
    ) -> Tuple[List[Dict], Dict[int, int]]:
        """Query textbook index across multiple class levels."""
        try:
            classes_to_search = self.get_prerequisite_classes(subject, student_class, mode)
            namespace = self.get_namespace(subject)
            
            all_chunks = []
            class_distribution = {}
            
            for class_level in classes_to_search:
                metadata_filter = {"class": class_level}
                if chapter:
                    metadata_filter["chapter"] = chapter
                
                results = self.textbook_db.query(
                    vector=query_embedding,
                    top_k=self.config.chunks_per_class,
                    namespace=namespace,
                    filter=metadata_filter
                )
                
                chunks_found = 0
                for match in results.get('matches', []):
                    if match.get('score', 0) >= 0.5:
                        metadata = match.get('metadata', {})
                        chunk_data = {
                            'text': metadata.get('text', ''),
                            'source': 'textbook',
                            'score': match.get('score', 0),
                            'class': class_level,
                            'chapter': metadata.get('chapter'),
                            'page': metadata.get('page_number')
                        }
                        all_chunks.append(chunk_data)
                        chunks_found += 1
                
                if chunks_found > 0:
                    class_distribution[class_level] = chunks_found
            
            # Sort by score
            all_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            return all_chunks, class_distribution
            
        except Exception as e:
            logger.error(f"❌ Textbook query failed: {e}")
            return [], {}
    
    def query_llm_cache(self, query_embedding: List[float], subject: str) -> List[Dict]:
        """Query LLM-generated answers cache."""
        try:
            if not self.llm_db or not self.llm_db.index:
                return []
            
            results = self.llm_db.query(
                vector=query_embedding,
                subject=subject,
                top_k=self.config.llm_top_k
            )
            
            llm_chunks = []
            for match in results.get('matches', []):
                if match.get('score', 0) >= self.config.llm_similarity_threshold:
                    metadata = match.get('metadata', {})
                    chunk_data = {
                        'text': metadata.get('answer', ''),
                        'source': 'llm_generated',
                        'score': match.get('score', 0),
                        'topic': metadata.get('topic', 'general'),
                        'quality_score': metadata.get('quality_score', 0.9)
                    }
                    llm_chunks.append(chunk_data)
            
            return llm_chunks
            
        except Exception as e:
            logger.warning(f"LLM cache query failed: {e}")
            return []
    
    def query_web_content(self, query_embedding: List[float], subject: str, student_class: int) -> List[Dict]:
        """Query web content index for supplementary information."""
        try:
            if not self.web_db or not self.web_db.index:
                return []
            
            results = self.web_db.query(
                vector=query_embedding,
                top_k=self.config.web_top_k,
                filter={"subject": subject}
            )
            
            web_chunks = []
            for match in results.get('matches', []):
                if match.get('score', 0) >= 0.5:
                    metadata = match.get('metadata', {})
                    chunk_data = {
                        'text': metadata.get('text', ''),
                        'source': 'web',
                        'score': match.get('score', 0),
                        'url': metadata.get('url', 'N/A')
                    }
                    web_chunks.append(chunk_data)
            
            return web_chunks
            
        except Exception as e:
            logger.warning(f"Web content query failed: {e}")
            return []
    
    def get_status(self) -> Dict:
        """Get service status for Intel endpoint."""
        return {
            "service": self.config.component_name,
            "intel_optimized": self.config.intel_optimized,
            "embedding_model": self.config.embedding_model,
            "indices": ["textbook", "web", "llm_cache"]
        }


# Singleton instance
retrieval_service = RetrievalService()
