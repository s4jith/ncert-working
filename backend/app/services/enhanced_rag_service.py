"""
Enhanced Multi-Index RAG Service

Implements intelligent cross-index retrieval:
- Basic Mode: Current class + relevant lower classes (textbook only)
- Deep Dive Mode: From fundamentals (earliest class) + web content for comprehensive understanding
- Triple-Index: Textbook + Web Scraped + LLM Generated content
"""

from app.services.gemini_service import gemini_service
from app.db.mongo import pinecone_db, pinecone_web_db, pinecone_llm_db
from app.services.llm_storage_service import llm_storage_service
from app.services.web_scraper_service import web_scraper_service
import logging
import re
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """
    Enhanced RAG service with multi-index progressive learning.
    
    Features:
    - Context-aware retrieval from multiple class levels
    - Two modes: Basic (quick answers) and Deep Dive (comprehensive from fundamentals)
    - Intelligent namespace/index routing
    """
    
    def __init__(self):
        self.gemini = gemini_service
        self.textbook_db = pinecone_db  # ncert-all-subjects index
        self.web_db = pinecone_web_db    # ncert-web-content index
        self.llm_db = pinecone_llm_db    # ncert-llm index (NEW)
        
        # Storage and scraping services
        self.llm_storage = llm_storage_service
        self.web_scraper = web_scraper_service
        
        # CRITICAL FIX: Use same embedding model as data upload
        # Data was uploaded using sentence-transformers, so we must use it for queries too!
        self.embedding_model_name = 'models/text-embedding-004'
        logger.info("✅ RAG Service: Using Gemini text-embedding-004 for embeddings")
        logger.info("✅ Triple-Index System: Textbook + Web + LLM content")
        
        # Subject to namespace mapping for ncert-all-subjects index
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
        
        # Class ranges for each subject
        self.subject_class_ranges = {
            "Mathematics": list(range(5, 13)),  # Class 5-12
            "Physics": list(range(11, 13)),     # Class 11-12
            "Chemistry": list(range(11, 13)),    # Class 11-12
            "Biology": list(range(11, 13)),      # Class 11-12
            "Social Science": list(range(5, 11)), # Class 5-10
            "History": list(range(5, 13)),       # Class 5-12
            "Geography": list(range(5, 13)),     # Class 5-12
            "Civics": list(range(5, 11)),        # Class 5-10
            "Economics": list(range(9, 13)),     # Class 9-12
            "English": list(range(5, 13)),       # Class 5-12
            "Hindi": list(range(5, 13))          # Class 5-12
        }

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini text-embedding-004.
        
        CRITICAL: Must use same model as PDF upload for retrieval to work!
        Returns 768-dimensional embedding vector.
        """
        try:
            # Configure API key before embedding generation
            from app.services.gemini_key_manager import gemini_key_manager
            api_key = gemini_key_manager.get_available_key()
            genai.configure(api_key=api_key)
            
            result = genai.embed_content(
                model=self.embedding_model_name,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise


    def _clean_markdown_formatting(self, text: str) -> str:
        """
        Clean markdown formatting to make text more readable for display.
        Converts markdown to plain text with proper formatting.
        """
        if not text:
            return text
        
        # Convert **bold** to plain text
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Convert *italic* to plain text
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Convert bullet points with * to proper bullets
        text = re.sub(r'^\s*\*\s+', '• ', text, flags=re.MULTILINE)
        
        # Convert numbered lists (1. 2. 3.) to better formatting  
        text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
        
        # Clean up excessive newlines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove any remaining markdown escape characters
        text = text.replace('\\*', '*')
        
        return text.strip()
    
    def get_namespace(self, subject: str) -> str:
        """Get Pinecone namespace for subject"""
        return self.subject_namespaces.get(subject, subject.lower().replace(" ", "_"))
    
    def get_prerequisite_classes(
        self,
        subject: str,
        student_class: int,
        mode: str = "basic"
    ) -> List[int]:
        """
        Get list of classes to search based on mode.
        
        Args:
            subject: Subject name
            student_class: Student's current class
            mode: "basic" (current + recent lower) or "deepdive" (all from fundamentals)
        
        Returns:
            List of class numbers to search, ordered from earliest to current
        """
        available_classes = self.subject_class_ranges.get(subject, list(range(5, 13)))
        available_classes = [c for c in available_classes if c <= student_class]
        
        if mode == "basic":
            # Basic mode: Current class + 2 previous classes
            # Example: Class 10 → [8, 9, 10]
            prerequisite_range = 2
            start_class = max(available_classes[0], student_class - prerequisite_range)
            return [c for c in available_classes if start_class <= c <= student_class]
        
        else:  # deepdive mode
            # Deep dive: ALL classes from start to current
            # Example: Class 10 Math → [5, 6, 7, 8, 9, 10]
            return available_classes
    
    def query_multi_class(
        self,
        query_text: str,
        subject: str,
        student_class: int,
        chapter: Optional[int] = None,
        mode: str = "basic",
        chunks_per_class: int = 5,
        query_embedding: Optional[List[float]] = None
    ) -> Tuple[List[Dict], Dict[int, int]]:
        """
        Query across multiple class levels for progressive learning.
        
        Args:
            query_text: Student's question
            subject: Subject name
            student_class: Current class level
            chapter: Optional chapter filter (None for all chapters)
            mode: "basic" or "deepdive"
            chunks_per_class: Max chunks per class level
        
        Returns:
            Tuple of (chunks, class_distribution)
        """
        try:
            # Get embedding using sentence-transformers (CRITICAL: Must match data upload model!)
            if query_embedding is None:
                query_embedding = self.generate_embedding(query_text)
            
            # Get classes to search
            classes_to_search = self.get_prerequisite_classes(subject, student_class, mode)
            logger.info(f"🔍 {mode.upper()} mode: Searching classes {classes_to_search} for {subject}")
            
            # Get namespace
            namespace = self.get_namespace(subject)
            
            # Query each class level
            all_chunks = []
            class_distribution = {}
            
            for class_level in classes_to_search:
                # Build metadata filter
                # Pinecone stores class_level as INTEGER (from pdf_processor.py)
                metadata_filter = {
                    "class_level": {"$eq": class_level},  # Integer as stored in pdf_processor
                    "subject": subject
                }
                
                if chapter is not None:
                    metadata_filter["chapter_number"] = chapter  # Integer as stored in pdf_processor
                
                try:
                    # Query textbook index with namespace
                    results = self.textbook_db.index.query(
                        namespace=namespace,
                        vector=query_embedding,
                        top_k=chunks_per_class,
                        filter=metadata_filter,
                        include_metadata=True
                    )
                    
                    # Extract matches
                    matches = results.get('matches', [])
                    class_chunks = 0
                    
                    for match in matches:
                        score = match.get('score', 0)
                        
                        # Dynamic threshold based on mode
                        threshold = 0.3 if mode == "basic" else 0.2
                        
                        if score >= threshold:
                            metadata = match.get('metadata', {})
                            chunk_data = {
                                'text': metadata.get('text', ''),
                                'class': class_level,
                                'subject': subject,
                                'chapter': metadata.get('chapter'),
                                'page': metadata.get('page'),
                                'score': score,
                                'source': 'textbook'
                            }
                            all_chunks.append(chunk_data)
                            class_chunks += 1
                    
                    if class_chunks > 0:
                        class_distribution[class_level] = class_chunks
                        logger.info(f"  ✓ Class {class_level}: {class_chunks} chunks (scores: {[round(m['score'], 2) for m in matches[:3]]})")
                
                except Exception as class_error:
                    logger.warning(f"  ✗ Class {class_level} query failed: {class_error}")
                    continue
            
            # Sort chunks: earlier classes first (for progressive building)
            all_chunks.sort(key=lambda x: (x['class'], -x['score']))
            
            logger.info(f"📊 Total chunks retrieved: {len(all_chunks)} from {len(class_distribution)} class levels")
            
            return all_chunks, class_distribution
            
        except Exception as e:
            logger.error(f"❌ Multi-class query failed: {e}")
            return [], {}
    
    def query_web_content(
        self,
        query_text: str,
        subject: str,
        student_class: int,
        top_k: int = 10,
        query_embedding: Optional[List[float]] = None
    ) -> List[Dict]:
        """
        Query web content index for additional context (DeepDive mode).
        
        Args:
            query_text: Student's question
            subject: Subject name
            student_class: Current class level
            top_k: Number of results
        
        Returns:
            List of web content chunks
        """
        try:
            if not self.web_db or not self.web_db.index:
                logger.info("ℹ️ Web content DB not available")
                return []
            
            # Generate embedding using sentence-transformers (CRITICAL: Must match data upload model!)
            if query_embedding is None:
                query_embedding = self.generate_embedding(query_text)
            
            # Query web content index
            # Note: Web content may use broader metadata structure
            metadata_filter = {
                "subject": subject,
                # Don't filter by class for web content - get broader context
            }
            
            results = self.web_db.query(
                vector=query_embedding,
                top_k=top_k,
                filter=metadata_filter
            )
            
            web_chunks = []
            for match in results.get('matches', []):
                if match.get('score', 0) >= 0.5:  # Higher threshold for web content
                    metadata = match.get('metadata', {})
                    chunk_data = {
                        'text': metadata.get('text', ''),
                        'source': 'web',
                        'score': match.get('score', 0),
                        'url': metadata.get('url', 'N/A')
                    }
                    web_chunks.append(chunk_data)
            
            logger.info(f"🌐 Web content: {len(web_chunks)} chunks retrieved")
            return web_chunks
            
        except Exception as e:
            logger.warning(f"Web content query failed: {e}")
            return []
    
    def query_llm_content(
        self,
        query_text: str,
        subject: str,
        top_k: int = 3,
        similarity_threshold: float = 0.75,
        query_embedding: Optional[List[float]] = None
    ) -> List[Dict]:
        """
        Query stored LLM-generated answers for similar questions.
        
        Args:
            query_text: Student's question
            subject: Subject name
            top_k: Number of results
            similarity_threshold: Minimum similarity score (0.0-1.0) to reuse answer
        
        Returns:
            List of LLM-generated answer chunks
        """
        try:
            if not self.llm_db or not self.llm_db.index:
                logger.debug("LLM content DB not available")
                return []
            
            # Generate embedding using sentence-transformers
            if query_embedding is None:
                query_embedding = self.generate_embedding(query_text)
            
            # Query LLM content index
            results = self.llm_db.query(
                vector=query_embedding,
                subject=subject,
                top_k=top_k
            )
            
            # Log what we found (for debugging)
            all_matches = results.get('matches', [])
            if all_matches:
                top_scores = [f"{m.get('score', 0):.3f}" for m in all_matches[:3]]
                logger.info(f"💡 LLM index check: Found {len(all_matches)} similar answers (top scores: {top_scores})")
            
            llm_chunks = []
            for match in results.get('matches', []):
                # Use configurable threshold for LLM reuse
                if match.get('score', 0) >= similarity_threshold:
                    metadata = match.get('metadata', {})
                    
                    # Increment usage count
                    self.llm_db.increment_usage(match['id'], subject)
                    
                    chunk_data = {
                        'text': metadata.get('answer', ''),
                        'source': 'llm_generated',
                        'score': match.get('score', 0),
                        'topic': metadata.get('topic', 'general'),
                        'quality_score': metadata.get('quality_score', 0.9),
                        'usage_count': metadata.get('usage_count', 0) + 1
                    }
                    llm_chunks.append(chunk_data)
            
            if llm_chunks:
                scores_list = [f"{c['score']:.2f}" for c in llm_chunks]
                logger.info(f"💡 LLM content: {len(llm_chunks)} stored answers retrieved (scores: {scores_list})")
            elif all_matches:
                # Found similar answers but below threshold
                logger.info(f"💡 LLM content: 0 answers met threshold ({similarity_threshold:.2f}+), will generate new answer")
            
            return llm_chunks
            
        except Exception as e:
            logger.warning(f"LLM content query failed: {e}")
            return []
    
    def generate_basic_answer(
        self,
        question: str,
        textbook_chunks: List[Dict],
        class_distribution: Dict[int, int],
        student_class: int,
        subject: str
    ) -> str:
        """
        Generate basic mode answer using textbook content from multiple classes.
        
        Args:
            question: Student's question
            textbook_chunks: Retrieved chunks from multiple classes
            class_distribution: Number of chunks per class
            student_class: Student's current class
            subject: Subject name
        
        Returns:
            Generated answer
        """
        if not textbook_chunks:
            # Fallback: Try to answer with general knowledge if RAG fails
            logger.info("⚠️ No RAG content found (Basic Mode). Attempting general knowledge fallback.")
            fallback_prompt = f"""You are a helpful tutor for Class {student_class} {subject} students.
            The student asked: "{question}"
            
            I could not find specific textbook content for this query in the vector database.
            Please answer the question using your general knowledge. 
            Start by saying: "I couldn't find this specific topic in your uploaded textbooks, but here is a general explanation:"
            Keep it simple and suitable for Class {student_class}.
            """
            return self.gemini.generate_response(fallback_prompt)
        
        # Build context with class markers
        context_parts = []
        current_class = None
        
        for chunk in textbook_chunks[:15]:  # Limit to top 15 chunks
            chunk_class = chunk.get('class')
            
            # Add class header when switching classes
            if chunk_class != current_class:
                if chunk_class < student_class:
                    context_parts.append(f"\n**FROM CLASS {chunk_class} (Foundation):**\n")
                else:
                    context_parts.append(f"\n**FROM CLASS {chunk_class}:**\n")
                current_class = chunk_class
            
            context_parts.append(chunk['text'])
        
        combined_context = "\n\n".join(context_parts)
        
        # Build progressive note
        classes_used = sorted(class_distribution.keys())
        if len(classes_used) > 1:
            progressive_note = f"(Using content from Classes {', '.join(map(str, classes_used))} to build complete understanding)"
        else:
            progressive_note = ""
        
        # Detect language of question for multilingual response
        lang_instruction = ""
        try:
            from app.services.openvino_multilingual_service import multilingual_service
            lang, confidence = multilingual_service.detect_language_with_confidence(question)
            lang_names = {"hi": "Hindi", "ur": "Urdu", "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi"}
            if lang != "en" and confidence > 0.5 and lang in lang_names:
                lang_instruction = f"\n6. IMPORTANT: The question is in {lang_names[lang]}. You MUST respond entirely in {lang_names[lang]} using the same script."
                logger.info(f"   🌐 Detected {lang_names[lang]} input, will respond in same language")
        except Exception as e:
            logger.debug(f"Language detection skipped: {e}")
        
        # Generate answer
        prompt = f"""You are a helpful tutor for Class {student_class} {subject} students.

STUDENT QUESTION: {question}

TEXTBOOK CONTENT (Multiple Classes):
{combined_context}

{progressive_note}

INSTRUCTIONS:
1. Answer the question using ONLY the textbook content provided
2. If content is from multiple classes, build the answer progressively:
   - Start with foundational concepts from earlier classes
   - Build up to current class level understanding
3. Keep the answer clear and appropriate for Class {student_class} students
4. Use examples from the textbook if available
5. If the content from earlier classes helps explain basics, mention it naturally{lang_instruction}

Generate a clear, helpful answer:"""
        
        answer = self.gemini.generate_response(prompt)
        logger.info(f"✓ Basic answer generated ({len(answer)} chars)")
        
        # Keep markdown formatting for ReactMarkdown frontend rendering
        # answer = self._clean_markdown_formatting(answer)  # DISABLED - frontend uses ReactMarkdown
        
        return answer
    
    def generate_deepdive_answer(
        self,
        question: str,
        textbook_chunks: List[Dict],
        web_chunks: List[Dict],
        class_distribution: Dict[int, int],
        student_class: int,
        subject: str
    ) -> str:
        """
        Generate comprehensive deep dive answer starting from fundamentals.
        
        Args:
            question: Student's question
            textbook_chunks: Retrieved chunks from all prerequisite classes
            web_chunks: Retrieved web content chunks
            class_distribution: Number of textbook chunks per class
            student_class: Student's current class
            subject: Subject name
        
        Returns:
            Comprehensive answer
        """
        if not textbook_chunks and not web_chunks:
            return f"I couldn't find enough information to provide a comprehensive answer. Try asking about specific topics from your {subject} curriculum!"
        
        # Build layered context
        context_sections = []
        
        # Section 1: Textbook content (progressive from fundamentals)
        if textbook_chunks:
            textbook_context = []
            classes_used = sorted(set(chunk.get('class') for chunk in textbook_chunks))
            
            context_sections.append(f"**TEXTBOOK CONTENT (Classes {', '.join(map(str, classes_used))}):**\n")
            
            # Group by class for progressive building
            for class_level in classes_used:
                class_chunks = [c for c in textbook_chunks if c.get('class') == class_level][:5]
                
                if class_level < student_class:
                    textbook_context.append(f"\n--- Foundation from Class {class_level} ---")
                else:
                    textbook_context.append(f"\n--- Class {class_level} ---")
                
                for chunk in class_chunks:
                    textbook_context.append(chunk['text'])
            
            context_sections.append("\n\n".join(textbook_context))
        
        # Section 2: Web content (additional background)
        if web_chunks:
            context_sections.append("\n\n**ADDITIONAL CONTEXT (Background Information):**\n")
            web_context = [chunk['text'] for chunk in web_chunks[:5]]
            context_sections.append("\n\n".join(web_context))
        
        combined_context = "\n\n".join(context_sections)
        
        # Build comprehensive prompt
        earliest_class = min(class_distribution.keys()) if class_distribution else student_class
        
        # Detect language of question for multilingual response
        lang_instruction = ""
        try:
            from app.services.openvino_multilingual_service import multilingual_service
            lang, confidence = multilingual_service.detect_language_with_confidence(question)
            lang_names = {"hi": "Hindi", "ur": "Urdu", "ta": "Tamil", "te": "Telugu", "bn": "Bengali", "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi"}
            if lang != "en" and confidence > 0.5 and lang in lang_names:
                lang_instruction = f"\n7. IMPORTANT: The question is in {lang_names[lang]}. You MUST respond entirely in {lang_names[lang]} using the same script."
                logger.info(f"   🌐 Detected {lang_names[lang]} input, will respond in same language")
        except Exception as e:
            logger.debug(f"Language detection skipped: {e}")
        
        prompt = f"""You are an expert tutor providing a COMPREHENSIVE explanation for a Class {student_class} {subject} student in DEEP DIVE mode.

STUDENT QUESTION: {question}

CONTENT (from Classes {earliest_class} to {student_class} + additional resources):
{combined_context}

DEEP DIVE MODE INSTRUCTIONS:
1. **Start from Fundamentals**: Begin with the most basic concept from the earliest class
2. **Progressive Building**: Build understanding step-by-step through class levels
3. **Comprehensive Coverage**: Address the "Wh-questions" - What, Why, When, Where, How (as applicable)
4. **Structure**:
   - 🌱 **Fundamentals** (if using content from Classes {earliest_class}-{student_class-1})
   - 📚 **Core Concept** (Class {student_class} level understanding)
   - 🔍 **Deep Dive** (comprehensive explanation with examples, applications, significance)
   - 💡 **Key Takeaways** (summarize main points)
5. **Make it engaging**: Use analogies, examples, and clear explanations
6. **Appropriate language**: Suitable for Class {student_class} students but comprehensive{lang_instruction}

Generate a thorough, well-structured deep dive explanation:"""
        
        answer = self.gemini.generate_response(prompt)
        logger.info(f"✓ Deep dive answer generated ({len(answer)} chars)")
        
        # Keep markdown formatting for ReactMarkdown frontend rendering
        # answer = self._clean_markdown_formatting(answer)  # DISABLED - frontend uses ReactMarkdown
        
        return answer
    
    def generate_answer_from_multiple_sources(
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
        Generate answer using triple-index system (Textbook + LLM + Web).
        Prioritizes textbook content, enriches with LLM answers, supplements with web content.
        
        Args:
            question: Student's question
            textbook_chunks: Retrieved textbook chunks
            llm_chunks: Retrieved LLM-generated answer chunks
            web_chunks: Retrieved web content chunks
            class_distribution: Number of textbook chunks per class
            student_class: Student's current class
            subject: Subject name
            mode: "basic" or "deepdive"
        
        Returns:
            Generated answer
        """
        if not textbook_chunks and not llm_chunks and not web_chunks:
            # Fallback: Try to answer with general knowledge if RAG fails, but warn the user
            logger.info("⚠️ No RAG content found. Attempting general knowledge fallback.")
            fallback_prompt = f"""You are an expert tutor for Class {student_class} {subject}.
            The student asked: "{question}"
            
            I could not find specific textbook content for this query. 
            Please answer the question using your general knowledge, but explicitly mention that this information is based on general principles and not directly from the specific NCERT textbook chapters.
            Keep the explanation simple, accurate, and suitable for a Class {student_class} student.
            """
            return self.gemini.generate_response(fallback_prompt)
        
        # Build multi-source context
        context_sections = []
        
        # PRIORITY 1: Textbook Content (Most Important)
        if textbook_chunks:
            classes_used = sorted(set(chunk.get('class') for chunk in textbook_chunks))
            context_sections.append(f"**PRIMARY SOURCE - NCERT Textbook (Classes {', '.join(map(str, classes_used))}):**\n")
            
            textbook_context = []
            for chunk in textbook_chunks[:10]:
                class_level = chunk.get('class', student_class)
                textbook_context.append(f"[Class {class_level}] {chunk['text']}")
            
            context_sections.append("\n\n".join(textbook_context))
        
        # PRIORITY 2: Previously Generated Explanations (High Quality)
        if llm_chunks:
            context_sections.append("\n\n**REFERENCE - Previously Generated Explanations:**\n")
            
            llm_context = []
            for chunk in llm_chunks[:2]:
                topic = chunk.get('topic', 'general')
                score = chunk.get('score', 0)
                llm_context.append(f"[Topic: {topic}, Relevance: {score:.2f}]\n{chunk['text']}")
            
            context_sections.append("\n\n".join(llm_context))
        
        # PRIORITY 3: Web Resources (Supplementary)
        if web_chunks:
            context_sections.append("\n\n**SUPPLEMENTARY - Web Resources:**\n")
            
            web_context = []
            for chunk in web_chunks[:5]:
                source_url = chunk.get('url', 'N/A')
                web_context.append(f"[Source: {source_url[:50]}...]\n{chunk['text']}")
            
            context_sections.append("\n\n".join(web_context))
        
        combined_context = "\n\n".join(context_sections)
        
        # Build comprehensive prompt
        mode_description = "COMPREHENSIVE" if mode == "deepdive" else "FOCUSED"
        
        prompt = f"""You are an expert NCERT tutor for Class {student_class} {subject} providing a {mode_description} explanation.

**STUDENT QUESTION:** {question}

**AVAILABLE SOURCES (in priority order):**
{combined_context}

**ANSWER GENERATION INSTRUCTIONS:**

1. **Primary Source**: Base your answer on NCERT textbook content (if available)
2. **Enhancement**: Use previously generated explanations for clarity and additional insights
3. **Enrichment**: Add web resources for examples, applications, or additional context
4. **NO HALLUCINATION**: Only use information provided in the sources above
5. **Clear Structure**: 
   {'- Start from fundamentals' if mode == 'deepdive' else '- Direct and concise'}
   - Use headings, bullet points, and examples
   - Appropriate for Class {student_class} students
6. **Source Integration**: Smoothly blend information from all sources
7. **Educational Focus**: Emphasize understanding, not just facts

Generate a {'comprehensive' if mode == 'deepdive' else 'clear and focused'} answer:"""
        
        answer = self.gemini.generate_response(prompt)
        
        # Log sources used
        sources_summary = f"Textbook: {len(textbook_chunks)}, LLM: {len(llm_chunks)}, Web: {len(web_chunks)}"
        logger.info(f"✅ Answer generated ({len(answer)} chars) from {sources_summary}")
        
        # Keep markdown formatting for ReactMarkdown frontend rendering
        # answer = self._clean_markdown_formatting(answer)  # DISABLED - frontend uses ReactMarkdown
        
        return answer
    
    # Main public methods
    
    def answer_question_basic(
        self,
        question: str,
        subject: str,
        student_class: int,
        chapter: Optional[int] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Answer question in BASIC mode with triple-index system.
        Queries: Textbook + Web + LLM content.
        
        Args:
            question: Student's question
            subject: Subject name
            student_class: Current class level
            chapter: Optional chapter filter
        
        Returns:
            Tuple of (answer, source_chunks)
        """
        logger.info(f"📚 BASIC MODE (Triple-Index): Class {student_class} {subject}")
        logger.info(f"   Question: {question[:100]}...")
        
        # 0. Generate embedding ONCE for all queries
        try:
            query_embedding = self.generate_embedding(question)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return "I'm having trouble understanding that right now. Please try again.", []

        # 1. Query textbook content (primary source)
        textbook_chunks, class_dist = self.query_multi_class(
            query_text=question,
            subject=subject,
            student_class=student_class,
            chapter=chapter,
            mode="basic",
            chunks_per_class=5,
            query_embedding=query_embedding
        )
        
        # 2. Query stored LLM answers
        llm_chunks = self.query_llm_content(
            query_text=question,
            subject=subject,
            top_k=2,
            query_embedding=query_embedding
        )
        
        # 🎯 CACHE HIT: Return cached answer directly if high similarity
        if llm_chunks and llm_chunks[0]['score'] >= 0.95:
            cached_answer = llm_chunks[0]['text']
            logger.info(f"🎯 CACHE HIT! Using cached answer (similarity: {llm_chunks[0]['score']:.3f}, topic: {llm_chunks[0].get('topic', 'N/A')})")
            logger.info(f"   Saved 1 Gemini API call (answer length: {len(cached_answer)} chars)")
            
            # Return cached answer with source information
            source_chunks = textbook_chunks + llm_chunks
            return cached_answer, source_chunks
        
        # 3. Query web content
        web_chunks = self.query_web_content(
            query_text=question,
            subject=subject,
            student_class=student_class,
            top_k=3,
            query_embedding=query_embedding
        )
        
        # 4. Check if we need more content via web scraping
        total_chunks = len(textbook_chunks) + len(web_chunks)
        if self.web_scraper.should_scrape(total_chunks, threshold=5):
            # Extract topic and trigger scraping
            topic = self.llm_storage._extract_topic(question)
            logger.info(f"🌐 Triggering web scraping for topic: {topic}")
            self.web_scraper.scrape_topic(subject, topic, student_class, max_sources=2)
        
        # Combine all sources
        all_chunks = textbook_chunks + llm_chunks + web_chunks
        
        # Generate answer from multiple sources
        answer = self.generate_answer_from_multiple_sources(
            question=question,
            textbook_chunks=textbook_chunks,
            llm_chunks=llm_chunks,
            web_chunks=web_chunks,
            class_distribution=class_dist,
            student_class=student_class,
            subject=subject,
            mode="basic"
        )
        
        # Store answer if high quality
        if self.llm_storage._should_store_answer(answer):
            topic = self.llm_storage._extract_topic(question)
            self.llm_storage.store_answer(
                question=question,
                answer=answer,
                subject=subject,
                class_level=student_class,
                topic=topic,
                quality_score=0.9
            )
        
        return answer, all_chunks
    
    def answer_annotation_basic(
        self,
        question: str,
        subject: str,
        student_class: int,
        chapter: Optional[int] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Answer annotation request with LOWER similarity threshold for LLM reuse.
        
        Annotations are often similar concepts worded differently, so we use
        a lower threshold (0.65 vs 0.75) to reuse existing answers more aggressively.
        
        EDGE CASE HANDLING:
        - If no content found in current class, searches previous classes (foundation)
        - If still no content, falls back to Gemini's general knowledge with disclaimer
        
        Args:
            question: Annotation question
            subject: Subject name
            student_class: Current class level
            chapter: Optional chapter filter
        
        Returns:
            Tuple of (answer, source_chunks)
        """
        logger.info(f"📝 ANNOTATION MODE (Lower threshold): Class {student_class} {subject}")
        logger.info(f"   Question: {question[:100]}...")
        
        # 1. Query textbook content (primary source)
        textbook_chunks, class_dist = self.query_multi_class(
            query_text=question,
            subject=subject,
            student_class=student_class,
            chapter=chapter,
            mode="basic",
            chunks_per_class=5
        )
        
        # 2. Query stored LLM answers with LOWER threshold for annotations
        llm_chunks = self.query_llm_content(
            query_text=question,
            subject=subject,
            top_k=3,
            similarity_threshold=0.65  # Lower threshold for annotation reuse
        )
        
        # 🎯 CACHE HIT: Return cached answer directly if high similarity
        if llm_chunks and llm_chunks[0]['score'] >= 0.90:  # Slightly lower for annotations (0.90 vs 0.95)
            cached_answer = llm_chunks[0]['text']
            logger.info(f"🎯 CACHE HIT! Using cached answer (similarity: {llm_chunks[0]['score']:.3f}, topic: {llm_chunks[0].get('topic', 'N/A')})")
            logger.info(f"   Saved 1 Gemini API call (answer length: {len(cached_answer)} chars)")
            
            # Return cached answer with source information
            source_chunks = textbook_chunks + llm_chunks
            return cached_answer, source_chunks
        
        # 3. Query web content (optional)
        web_chunks = self.query_web_content(
            query_text=question,
            subject=subject,
            student_class=student_class,
            top_k=2
        )
        
        # EDGE CASE 1: No content found - Try progressive search (earlier classes)
        if not textbook_chunks and not llm_chunks:
            logger.warning(f"⚠️ EDGE CASE: No content found for '{question[:50]}...' in Class {student_class}")
            logger.info(f"🔄 Attempting progressive search in Classes {max(5, student_class-3)}-{student_class-1}...")
            
            # Try searching previous 3 classes for foundational content
            for prev_class in range(student_class - 1, max(4, student_class - 4), -1):
                logger.info(f"   Searching Class {prev_class}...")
                prev_chunks, prev_dist = self.query_multi_class(
                    query_text=question,
                    subject=subject,
                    student_class=prev_class,
                    chapter=None,  # Remove chapter filter for broader search
                    mode="basic",
                    chunks_per_class=5
                )
                
                if prev_chunks:
                    logger.info(f"✅ Found {len(prev_chunks)} chunks in Class {prev_class} (foundation content)")
                    textbook_chunks = prev_chunks
                    class_dist = prev_dist
                    break
        
        # Combine all sources
        all_chunks = textbook_chunks + llm_chunks + web_chunks
        
        # EDGE CASE 2: Still no content - Use Gemini fallback with disclaimer
        if not all_chunks:
            logger.warning(f"⚠️ EDGE CASE: No content in any class for '{question[:50]}...'")
            logger.info(f"🤖 Using Gemini fallback (general knowledge with disclaimer)")
            
            fallback_prompt = f"""The student asked: "{question}"

This topic doesn't appear to be explicitly covered in their Class {student_class} {subject} textbook.

Provide a simple, age-appropriate explanation suitable for Class {student_class} students:
1. Basic definition or concept (2-3 sentences)
2. One simple example
3. End with: "Note: This explanation is based on general {subject} knowledge. Check your textbook or ask your teacher for content specific to your Class {student_class} syllabus."

Keep it under 200 words and student-friendly."""
            
            answer = self.gemini.generate_response(fallback_prompt)
            # Keep markdown formatting for ReactMarkdown frontend rendering
            # answer = self._clean_markdown_formatting(answer)  # DISABLED - frontend uses ReactMarkdown
            
            logger.info(f"✓ Fallback answer generated ({len(answer)} chars)")
            return answer, []  # Return empty chunks to indicate fallback was used
        
        # Generate answer from multiple sources
        answer = self.generate_answer_from_multiple_sources(
            question=question,
            textbook_chunks=textbook_chunks,
            llm_chunks=llm_chunks,
            web_chunks=web_chunks,
            class_distribution=class_dist,
            student_class=student_class,
            subject=subject,
            mode="basic"
        )
        
        # Store answer if high quality
        if self.llm_storage._should_store_answer(answer):
            topic = self.llm_storage._extract_topic(question)
            self.llm_storage.store_answer(
                question=question,
                answer=answer,
                subject=subject,
                class_level=student_class,
                topic=topic,
                quality_score=0.9
            )
        
        return answer, all_chunks
    
    def answer_question_deepdive(
        self,
        question: str,
        subject: str,
        student_class: int,
        chapter: Optional[int] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Answer question in DEEP DIVE mode with triple-index system.
        Queries: Textbook (all classes) + Web + LLM content + auto-scraping.
        
        Args:
            question: Student's question
            subject: Subject name
            student_class: Current class level
            chapter: Optional chapter filter
        
        Returns:
            Tuple of (answer, combined_source_chunks)
        """
        logger.info(f"🔍 DEEP DIVE MODE (Triple-Index): Class {student_class} {subject}")
        logger.info(f"   Question: {question[:100]}...")
        logger.info(f"   Will search from fundamentals (earliest class) to current class")
        
        # 1. Query textbook content (all prerequisite classes)
        textbook_chunks, class_dist = self.query_multi_class(
            query_text=question,
            subject=subject,
            student_class=student_class,
            chapter=chapter,
            mode="deepdive",
            chunks_per_class=8  # More chunks per class for comprehensive coverage
        )
        
        # 2. Query stored LLM answers
        llm_chunks = self.query_llm_content(
            query_text=question,
            subject=subject,
            top_k=3
        )
        
        # 🎯 CACHE HIT: Return cached answer directly if high similarity
        if llm_chunks and llm_chunks[0]['score'] >= 0.95:
            cached_answer = llm_chunks[0]['text']
            logger.info(f"🎯 CACHE HIT! Using cached answer (similarity: {llm_chunks[0]['score']:.3f}, topic: {llm_chunks[0].get('topic', 'N/A')})")
            logger.info(f"   Saved 1 Gemini API call (answer length: {len(cached_answer)} chars)")
            
            # Return cached answer with source information
            source_chunks = textbook_chunks + llm_chunks
            return cached_answer, source_chunks
        
        # 3. Query web content for additional context
        web_chunks = self.query_web_content(
            query_text=question,
            subject=subject,
            student_class=student_class,
            top_k=10
        )
        
        # 4. Check if we need more content via web scraping
        total_chunks = len(textbook_chunks) + len(web_chunks)
        if self.web_scraper.should_scrape(total_chunks, threshold=8):
            # Extract topic and trigger scraping
            topic = self.llm_storage._extract_topic(question)
            logger.info(f"🌐 Triggering web scraping for topic: {topic}")
            self.web_scraper.scrape_topic(subject, topic, student_class, max_sources=3)
            
            # Re-query web content after scraping
            web_chunks = self.query_web_content(
                query_text=question,
                subject=subject,
                student_class=student_class,
                top_k=10
            )
        
        # Combine all sources
        all_chunks = textbook_chunks + llm_chunks + web_chunks
        
        # Generate comprehensive answer from multiple sources
        answer = self.generate_answer_from_multiple_sources(
            question=question,
            textbook_chunks=textbook_chunks,
            llm_chunks=llm_chunks,
            web_chunks=web_chunks,
            class_distribution=class_dist,
            student_class=student_class,
            subject=subject,
            mode="deepdive"
        )
        
        # Store answer if high quality
        if self.llm_storage._should_store_answer(answer):
            topic = self.llm_storage._extract_topic(question)
            self.llm_storage.store_answer(
                question=question,
                answer=answer,
                subject=subject,
                class_level=student_class,
                topic=topic,
                quality_score=0.95  # Higher score for deepdive answers
            )
        
        return answer, all_chunks


# Global instance
enhanced_rag_service = EnhancedRAGService()

