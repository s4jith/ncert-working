"""
RAG Service - Handles Retrieval-Augmented Generation using Pinecone + Gemini.
Production-grade implementation with strict RAG enforcement.
Supports progressive multi-class learning via namespace architecture.
"""

from app.services.gemini_service import gemini_service
from app.db.mongo import pinecone_db, namespace_db
import logging
import re

logger = logging.getLogger(__name__)


# Greeting patterns and responses (NO Gemini call)
GREETINGS = {
    "hi": ["hi", "hello", "hey", "yo", "hii", "hiiii", "hey there", "hi buddy", "helo", "hellow"],
    "bye": ["bye", "good bye", "goodbye", "see you", "see you later", "see ya", "cya"],
    "thanks": ["thank you", "thanks", "thankyou", "thx", "thank u"],
    "ok": ["ok", "okay", "fine", "good", "alright", "cool"],
    "how_are_you": ["how are you", "how r u", "what's up", "sup", "whats up", "wassup"]
}

GREETING_RESPONSES = {
    "hi": "Hey there! What do you want to learn today?",
    "bye": "See you soon! Keep learning!",
    "thanks": "You're welcome! Happy learning!",
    "ok": "Great! Is there anything else you'd like to learn?",
    "how_are_you": "I'm here and ready to help you learn!"
}

# Similarity threshold for RAG results
SIMILARITY_THRESHOLD = 0.3  # Lowered for better recall

# Keywords that indicate user wants broader/summary content (lower threshold needed)
BROAD_QUERY_KEYWORDS = [
    "note", "notes", "brief", "summary", "summarize", "overview", "explain",
    "about", "introduction", "what is", "describe", "tell me about",
    "in short", "short note", "briefly", "in brief", "key points"
]


class RAGService:
    """Service for RAG-based retrieval and answer generation with progressive learning support."""
    
    def __init__(self):
        self.gemini = gemini_service
        self.pinecone = pinecone_db  # Legacy DB
        self.namespace_db = namespace_db  # NEW: Namespace-based DB for progressive learning
    
    @staticmethod
    def detect_greeting(text: str) -> str | None:
        """
        Detect if user input is a greeting.
        Returns response if greeting detected, None otherwise.
        
        Args:
            text: User input (normalized)
        
        Returns:
            Greeting response or None
        """
        text_lower = text.lower().strip()
        
        for greeting_type, patterns in GREETINGS.items():
            for pattern in patterns:
                if text_lower == pattern or text_lower.startswith(pattern + " "):
                    return GREETING_RESPONSES[greeting_type]
        
        return None
    
    @staticmethod
    def is_broad_query(text: str) -> bool:
        """
        Detect if query is asking for broad/summary content.
        These queries should use lower threshold to get more context.
        
        Args:
            text: User query
        
        Returns:
            True if broad query detected
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in BROAD_QUERY_KEYWORDS)
    
    def query_with_rag(
        self,
        query_text: str,
        class_level: int,
        subject: str,
        chapter: int,
        mode: str,
        top_k: int = 10,  # Increased from 5 to 10 for better coverage
        min_score: float = None  # Optional minimum score threshold
    ) -> tuple[str, list[str]]:
        """
        Query Pinecone with embeddings and generate answer using Gemini.
        Implements strict RAG enforcement with greeting detection.
        
        Args:
            query_text: Student's highlighted text/question
            class_level: Class (5-10)
            subject: Subject name
            chapter: Chapter number
            mode: Explanation mode
            top_k: Number of chunks to retrieve
        
        Returns:
            Tuple of (answer, source_chunks)
        """
        try:
            # Step 1: Normalize input
            query_normalized = query_text.strip()
            
            # Step 2: Check for greetings (NO Gemini call)
            greeting_response = self.detect_greeting(query_normalized)
            if greeting_response:
                logger.info("Greeting detected - returning canned response")
                return greeting_response, []
            
            # Step 3: Adjust top_k for broad queries to get more context
            is_broad = self.is_broad_query(query_text)
            if is_broad and mode == "quick":
                top_k = 15  # Get more chunks for comprehensive coverage
                logger.info(f"📚 Broad query detected - retrieving {top_k} chunks for comprehensive answer")
            
            # Step 4: Generate embedding for query
            logger.info(f"Generating embedding for: {query_text[:50]}...")
            query_embedding = self.gemini.generate_embedding(query_text)
            
            # Step 5: Query Pinecone with metadata filter
            # Note: Metadata uses 'lesson_number' not 'chapter'
            # Note: 'class' is stored as STRING not integer
            metadata_filter = {
                "class": str(class_level),  # Convert to string to match uploaded metadata
                "subject": subject,
                # Map chapter to lesson_number (formatted as "01", "02", etc.)
                "lesson_number": f"{chapter:02d}"
            }
            
            logger.info(f"Querying Pinecone with filter: {metadata_filter}")
            results = self.pinecone.query(
                vector=query_embedding,
                top_k=top_k,
                filter=metadata_filter
            )
            
            # Step 6: Similarity check - strict threshold
            matches = results.get('matches', [])
            
            if not matches:
                logger.warning("No matching chunks found in Pinecone")
                return "No answer found in the book.", []
            
            # Log all match scores
            logger.info(f"Found {len(matches)} matches with scores: {[m.get('score', 0) for m in matches]}")
            
            # Smart threshold adjustment based on query type
            if min_score is not None:
                # If explicit min_score provided (e.g., Quick mode), use it
                score_threshold = min_score
            else:
                # Auto-adjust threshold based on query intent
                if self.is_broad_query(query_text):
                    score_threshold = SIMILARITY_THRESHOLD  # Lower threshold (0.3)
                    logger.info(f"📝 Broad query detected - using lower threshold: {score_threshold}")
                else:
                    score_threshold = 0.50  # Medium threshold for specific queries
                    logger.info(f"🎯 Specific query - using medium threshold: {score_threshold}")
            
            # For Quick mode specifically, apply smart threshold
            if mode == "quick":
                if self.is_broad_query(query_text):
                    # For broad queries in Quick mode, use medium threshold (not too low, not too high)
                    score_threshold = 0.45
                    logger.info(f"⚡ Quick mode + Broad query - adjusted threshold to: {score_threshold}")
                elif min_score is None:
                    # Specific queries in Quick mode should still be strict
                    score_threshold = 0.65
            
            logger.info(f"Using threshold: {score_threshold}")
            
            # Filter by similarity threshold
            valid_matches = [m for m in matches if m.get('score', 0) >= score_threshold]
            
            if not valid_matches:
                logger.warning(f"All matches below similarity threshold ({score_threshold})")
                # For Quick mode with high threshold, provide helpful message
                if min_score and min_score > SIMILARITY_THRESHOLD:
                    return "I couldn't find a direct answer in your textbook for this specific question. Try asking about topics directly covered in the chapter!", []
                return "No answer found in the book.", []
            
            # Step 6: Extract text chunks from valid results
            chunks = []
            for match in valid_matches:
                if 'metadata' in match and 'text' in match['metadata']:
                    text = match['metadata']['text']
                    # Filter out junk chunks (page numbers, headers, etc.)
                    if len(text) > 50 and not text.startswith('1000 m2000'):  # Skip pagination artifacts
                        chunks.append(text)
            
            logger.info(f"Extracted {len(chunks)} text chunks from valid matches")
            
            if not chunks:
                logger.warning("No text content in matched chunks")
                return "No answer found in the book.", []
            
            # Step 7: Combine chunks into context
            context = "\n\n---\n\n".join(chunks)
            logger.info(f"Context length: {len(context)} chars, Preview: {context[:150]}...")
            
            # Step 8: Generate answer using Gemini
            logger.info(f"Generating {mode} explanation using Gemini for Class {class_level}...")
            logger.info(f"Context preview: {context[:200]}...")
            
            try:
                answer = self.gemini.format_explanation(
                    context=context,
                    question=query_text,
                    mode=mode,
                    class_level=class_level  # Pass class level for language adjustment
                )
                logger.info(f"✓ Gemini response received: {len(answer)} chars - '{answer[:100]}...'")
            except Exception as e:
                logger.error(f"❌ Gemini generation failed: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                answer = "No answer found in the book."
            
            return answer, chunks
        
        except Exception as e:
            logger.error(f"❌ RAG query failed: {e}")
            raise
    
    def query_with_rag_progressive(
        self,
        query_text: str,
        class_level: int,
        subject: str,
        chapter: int,
        mode: str,
        top_k: int = 15,
        min_score: float = None
    ) -> tuple[str, list[str]]:
        """
        Query using progressive learning - access content from current and previous classes.
        Enables students to access foundational content from earlier classes.
        
        For example: Class 11 students can access Class 9-10 content for prerequisites.
        
        Args:
            query_text: Student's highlighted text/question
            class_level: Current class level (5-12)
            subject: Subject name (Mathematics, Physics, Chemistry, etc.)
            chapter: Current chapter number
            mode: Explanation mode ("quick" or "deepdive")
            top_k: Number of chunks to retrieve
            min_score: Optional minimum similarity score
        
        Returns:
            Tuple of (answer, source_chunks)
        """
        try:
            # Step 1: Normalize input
            query_normalized = query_text.strip()
            
            # Step 2: Check for greetings (NO Gemini call)
            greeting_response = self.detect_greeting(query_normalized)
            if greeting_response:
                logger.info("Greeting detected - returning canned response")
                return greeting_response, []
            
            # Step 3: Adjust top_k for broad queries
            is_broad = self.is_broad_query(query_text)
            if is_broad and mode == "quick":
                top_k = 20  # Get more chunks for comprehensive multi-class coverage
                logger.info(f"📚 Broad progressive query - retrieving {top_k} chunks across classes")
            
            # Step 4: Generate embedding for query
            logger.info(f"🎓 Progressive Query: Class {class_level} {subject}, Mode: {mode}")
            logger.info(f"Generating embedding for: {query_text[:50]}...")
            query_embedding = self.gemini.generate_embedding(query_text)
            
            # Step 5: Use progressive query from namespace DB
            # This automatically includes previous classes based on mode
            logger.info(f"Querying namespace DB with progressive learning...")
            results = self.namespace_db.query_progressive(
                vector=query_embedding,
                subject=subject,
                student_class=class_level,
                mode=mode,
                top_k=top_k
            )
            
            # Step 6: Similarity check
            matches = results.get('matches', [])
            logger.info(f"Got {len(matches)} total matches from progressive query")
            
            if not matches:
                logger.warning("No matches found")
                return "No answer found in the book.", []
            
            # Smart threshold detection
            threshold = SIMILARITY_THRESHOLD
            if is_broad or mode == "deepdive":
                threshold = 0.2  # Lower threshold for broad queries
                logger.info(f"Using relaxed threshold {threshold} for {'broad query' if is_broad else 'deepdive mode'}")
            
            if min_score is not None:
                threshold = min_score
                logger.info(f"Using custom threshold: {threshold}")
            
            # Filter by score
            valid_matches = [m for m in matches if m.get('score', 0) >= threshold]
            logger.info(f"Filtered to {len(valid_matches)} matches above threshold {threshold}")
            
            if not valid_matches:
                logger.warning(f"No matches above threshold {threshold}")
                return "No answer found in the book.", []
            
            # Log multi-class results for transparency
            classes_found = set()
            for match in valid_matches:
                metadata = match.get('metadata', {})
                class_str = metadata.get('class', 'unknown')
                classes_found.add(class_str)
            
            if len(classes_found) > 1:
                logger.info(f"📚 Multi-class results: Found content from classes {sorted(classes_found)}")
            
            # Step 7: Extract text chunks
            chunks = []
            for match in valid_matches:
                metadata = match.get('metadata', {})
                text = metadata.get('text', '')
                score = match.get('score', 0)
                match_class = metadata.get('class', 'unknown')
                
                logger.info(f"  Match from Class {match_class}: score={score:.3f}, text={text[:80]}...")
                
                if text and len(text) > 50 and not text.startswith('1000 m2000'):
                    chunks.append(text)
            
            logger.info(f"Extracted {len(chunks)} text chunks from valid matches")
            
            if not chunks:
                logger.warning("No text content in matched chunks")
                return "No answer found in the book.", []
            
            # Step 8: Combine chunks into context
            context = "\n\n---\n\n".join(chunks)
            logger.info(f"Context length: {len(context)} chars")
            
            # Step 9: Generate answer using Gemini
            # Include hint about multi-class if relevant
            if len(classes_found) > 1:
                logger.info(f"Generating explanation using content from classes: {sorted(classes_found)}")
                # Add metadata to help Gemini understand progressive context
                progressive_note = f"\n\n[Note: This answer includes foundational content from previous classes {sorted(classes_found)} to help build understanding.]"
                context = context + progressive_note
            
            logger.info(f"Generating {mode} explanation using Gemini for Class {class_level}...")
            
            try:
                answer = self.gemini.format_explanation(
                    context=context,
                    question=query_text,
                    mode=mode,
                    class_level=class_level
                )
                logger.info(f"✓ Gemini response received: {len(answer)} chars")
            except Exception as e:
                logger.error(f"❌ Gemini generation failed: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                answer = "No answer found in the book."
            
            return answer, chunks
        
        except Exception as e:
            logger.error(f"❌ Progressive RAG query failed: {e}")
            raise
    
    def retrieve_chapter_context(
        self,
        class_level: int,
        subject: str,
        chapter: int,
        max_chunks: int = 20
    ) -> str:
        """
        Retrieve full chapter context from Pinecone for MCQ generation.
        
        Args:
            class_level: Class (5-10)
            subject: Subject name
            chapter: Chapter number
            max_chunks: Maximum chunks to retrieve
        
        Returns:
            Combined chapter text
        """
        try:
            # Use a generic query to get chapter content
            dummy_query = f"{subject} chapter {chapter}"
            query_embedding = self.gemini.generate_embedding(dummy_query)
            
            metadata_filter = {
                "class": str(class_level),  # Convert to string
                "subject": subject,
                "lesson_number": f"{chapter:02d}"
            }
            
            results = self.pinecone.query(
                vector=query_embedding,
                top_k=max_chunks,
                filter=metadata_filter
            )
            
            # Extract and combine chunks
            chunks = []
            for match in results.get('matches', []):
                if 'metadata' in match and 'text' in match['metadata']:
                    chunks.append(match['metadata']['text'])
            
            if not chunks:
                raise ValueError(f"No content found for Class {class_level}, {subject}, Chapter {chapter}")
            
            return "\n\n".join(chunks)
        
        except Exception as e:
            logger.error(f"❌ Chapter context retrieval failed: {e}")
            raise
    
    def query_with_rag_deepdive(
        self,
        query_text: str,
        class_level: int,
        subject: str,
        chapter: int,
        top_k: int = 20
    ) -> tuple[str, list[str]]:
        """
        Query with DeepDive mode - comprehensive answers using textbook (multi-class) and web content.
        
        Uses progressive learning to access content from current and ALL prerequisite classes.
        Also searches web-scraped content for comprehensive background information.
        
        Args:
            query_text: Student's question
            class_level: Current class (5-12)
            subject: Subject name
            chapter: Current chapter number
            top_k: Number of chunks to retrieve from each source
        
        Returns:
            Tuple of (comprehensive_answer, combined_source_chunks)
        """
        try:
            logger.info(f"🔍 DeepDive mode for Class {class_level}: {query_text[:50]}...")
            
            # Check for greetings first
            greeting_response = self.detect_greeting(query_text)
            if greeting_response:
                return greeting_response, []
            
            # Generate embedding once for both queries
            query_embedding = self.gemini.generate_embedding(query_text)
            
            # Query textbook content with PROGRESSIVE LEARNING (all prerequisite classes)
            logger.info(f"Querying textbook DB with progressive learning (DeepDive mode)...")
            textbook_chunks = []
            classes_found = set()
            
            try:
                # Use namespace DB with deepdive mode for all prerequisite classes
                textbook_results = self.namespace_db.query_progressive(
                    vector=query_embedding,
                    subject=subject,
                    student_class=class_level,
                    mode="deepdive",  # Gets ALL prerequisite classes
                    top_k=top_k
                )
                
                # Extract textbook chunks
                for match in textbook_results.get('matches', []):
                    if match.get('score', 0) >= 0.2:  # Lower threshold for deepdive
                        metadata = match.get('metadata', {})
                        text = metadata.get('text', '')
                        match_class = metadata.get('class', 'unknown')
                        
                        if text and len(text) > 50:
                            textbook_chunks.append(text)
                            classes_found.add(match_class)
                
                logger.info(f"✓ Found {len(textbook_chunks)} textbook chunks from classes: {sorted(classes_found)}")
            except Exception as textbook_error:
                logger.error(f"Textbook DB query failed: {textbook_error}")
                # Don't fail completely, continue to try web content
            
            # Query web content (Pinecone index 2 - if available)
            web_chunks = []
            try:
                from app.db.mongo import pinecone_web_db
                if pinecone_web_db and pinecone_web_db.index:
                    logger.info(f"Querying web content DB...")
                    # For web content, use broader filter (topic-based, not chapter-specific)
                    web_filter = {
                        "class": str(class_level),
                        "subject": subject
                    }
                    web_results = pinecone_web_db.query(
                        vector=query_embedding,
                        top_k=top_k,
                        filter=web_filter
                    )
                    
                    for match in web_results.get('matches', []):
                        if match.get('score', 0) >= 0.5 and 'metadata' in match and 'text' in match['metadata']:
                            web_chunks.append(match['metadata']['text'])
                    
                    logger.info(f"✓ Found {len(web_chunks)} web content chunks")
                else:
                    logger.info("ℹ️ Web content DB not available yet")
            except Exception as web_error:
                logger.warning(f"Web content query failed: {web_error}")
            
            if not textbook_chunks and not web_chunks:
                logger.warning("No relevant content found in either database")
                return "I couldn't find enough information to answer this comprehensively. Try asking about specific topics from your chapter!", []
            
            # Combine contexts with clear separation
            combined_context = ""
            if textbook_chunks:
                # Note multi-class content if relevant
                if len(classes_found) > 1:
                    combined_context += f"**FROM YOUR TEXTBOOK (Classes {', '.join(sorted(classes_found))}):**\n\n"
                else:
                    combined_context += "**FROM YOUR TEXTBOOK:**\n\n"
                combined_context += "\n\n---\n\n".join(textbook_chunks)
            if web_chunks:
                if combined_context:
                    combined_context += "\n\n\n**ADDITIONAL CONTEXT (Background Information):**\n\n"
                combined_context += "\n\n---\n\n".join(web_chunks)
            
            # Generate comprehensive answer using special DeepDive prompt
            progressive_note = ""
            if len(classes_found) > 1:
                progressive_note = f"\nNote: This explanation builds on concepts from classes {', '.join(sorted(classes_found))}."
            
            deepdive_prompt = f"""You are an expert tutor for Class {class_level} students. A student has asked for a COMPREHENSIVE explanation.

QUESTION: {query_text}

CONTEXT (from textbook and additional sources):
{combined_context}{progressive_note}

DEEPDIVE MODE INSTRUCTIONS:
1. Provide a COMPREHENSIVE answer covering ALL relevant aspects
2. Address the "Wh-questions": What, Why, When, Where, Who, How (as applicable)
3. Start with a clear definition/overview
4. Explain the background and context
5. Discuss causes, effects, and significance
6. Include examples and connections
7. If using content from earlier classes, build progressively from fundamentals to current level
8. Structure with headers and bullet points for clarity
9. Use language appropriate for Class {class_level} students

Generate a thorough, well-structured explanation:"""
            
            answer = self.gemini.generate_response(deepdive_prompt)
            logger.info(f"✓ DeepDive answer generated: {len(answer)} chars")
            
            return answer, textbook_chunks + web_chunks
        
        except Exception as e:
            logger.error(f"❌ DeepDive query failed: {e}")
            raise


# Global RAG service instance
rag_service = RAGService()
