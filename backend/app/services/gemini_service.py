"""
Gemini Service - Handles all Google Gemini AI interactions with multi-key rotation.
"""

import google.generativeai as genai
from app.core.config import settings
from app.services.gemini_key_manager import gemini_key_manager
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini AI with automatic key rotation."""
    
    def __init__(self):
        # Don't configure API key here - will be set per request via key manager
        # Initialize Gemini 2.5 Flash model
        self.model_name = 'models/gemini-2.5-flash'
        logger.info(f"🚀 Gemini Service initialized with model: {self.model_name}")
        logger.info(f"🔑 Using multi-key rotation: {gemini_key_manager.get_quota_status()['total_keys']} keys available")
        
        # Initialize embedding model
        self.embedding_model = 'models/text-embedding-004'
    
    def _get_model_with_available_key(self, retry_count: int = 0):
        """
        Get a GenerativeModel instance with an available API key.
        
        Args:
            retry_count: Number of retries attempted (for recursive retry logic)
        
        Returns:
            Tuple of (model, key_info) for error handling
        """
        if retry_count >= len(gemini_key_manager.keys):
            # Tried all keys, none worked
            raise Exception(
                "❌ All Gemini API keys exhausted or rate limited! "
                f"Total capacity: {gemini_key_manager.get_quota_status()['total_capacity']} requests/day. "
                "Quotas reset at midnight Pacific Time."
            )
        
        api_key = gemini_key_manager.get_available_key()
        
        if not api_key:
            raise Exception(
                "❌ All Gemini API keys exhausted! "
                f"Total capacity: {gemini_key_manager.get_quota_status()['total_capacity']} requests/day. "
                "Quotas reset at midnight Pacific Time."
            )
        
        # Configure Gemini with the available key
        genai.configure(api_key=api_key)
        
        # Return model instance with current key index for error handling
        return genai.GenerativeModel(self.model_name), gemini_key_manager.current_key_index
    
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vector for text using Gemini embedding model.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector (list of floats)
        """
        try:
            # Configure API key before embedding generation
            from app.services.gemini_key_manager import gemini_key_manager
            api_key = gemini_key_manager.get_available_key()
            genai.configure(api_key=api_key)
            
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            raise
    
    def format_explanation(
        self, 
        context: str, 
        question: str, 
        mode: str,
        class_level: int = 6,
        retry_count: int = 0
    ) -> str:
        """
        Generate explanation using Gemini based on RAG context and mode.
        
        Args:
            context: RAG-retrieved context chunks
            question: Student's highlighted text/question
            mode: Explanation mode (simple/meaning/story/example/summary)
            class_level: Student's class level (5-10)
            retry_count: Number of retries attempted (internal use)
        
        Returns:
            Formatted explanation string
        """
        try:
            # Build mode-specific prompt with class level
            prompt = self._build_prompt(context, question, mode, class_level)
            
            # Get model with available API key
            model, key_index = self._get_model_with_available_key(retry_count)
            
            # Generate response
            response = model.generate_content(prompt)
            
            return response.text
        
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a 429 rate limit error
            if "429" in error_str and retry_count < len(gemini_key_manager.keys):
                logger.warning(f"⚠️  429 Rate limit hit. Rotating to next key (retry {retry_count + 1})...")
                
                # Force rotation to next key
                gemini_key_manager.current_key_index = (gemini_key_manager.current_key_index + 1) % len(gemini_key_manager.keys)
                
                # Retry with next key
                return self.format_explanation(context, question, mode, class_level, retry_count + 1)
            
            logger.error(f"❌ Gemini explanation failed: {e}")
            raise
    
    def generate_response(self, prompt: str, retry_count: int = 0) -> str:
        """
        Generate a simple text response from Gemini with automatic retry on 429 errors.
        
        Args:
            prompt: Input prompt
            retry_count: Number of retries attempted (internal use)
        
        Returns:
            Generated text response
        """
        try:
            # Get model with available API key
            model, key_index = self._get_model_with_available_key(retry_count)
            
            response = model.generate_content(prompt)
            return response.text
        
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a 429 rate limit error
            if "429" in error_str and retry_count < len(gemini_key_manager.keys):
                logger.warning(f"⚠️  429 Rate limit hit. Rotating to next key (retry {retry_count + 1})...")
                
                # Force rotation to next key
                gemini_key_manager.current_key_index = (gemini_key_manager.current_key_index + 1) % len(gemini_key_manager.keys)
                
                # Retry with next key
                return self.generate_response(prompt, retry_count + 1)
            
            logger.error(f"❌ Gemini generation failed: {e}")
            raise
    
    def _build_prompt(self, context: str, question: str, mode: str, class_level: int = 6) -> str:
        """Build prompt based on mode and class level to generate helpful answers."""
        
        # Class-level specific language instructions
        language_complexity = {
            5: "Use VERY SIMPLE words. Short sentences (5-7 words). Like talking to a 10-year-old. Use everyday examples.",
            6: "Use simple, clear language. Short sentences. Explain like to a 11-year-old. Use relatable examples.",
            7: "Use clear language. Medium sentences. Explain like to a 12-year-old. Use school-level examples.",
            8: "Use standard language. Can use some technical terms but explain them. Like talking to a 13-year-old.",
            9: "Use proper academic language. Can use technical terms with brief explanations. Like talking to a 14-year-old.",
            10: "Use academic language. Technical terms are okay. Detailed explanations. Like talking to a 15-year-old preparing for board exams."
        }
        
        language_instruction = language_complexity.get(class_level, language_complexity[6])
        
        base_instruction = f"""You are an AI tutor for NCERT Class {class_level} students.

CRITICAL RULES - STRICT RAG (Retrieval-Augmented Generation):
1. ⚠️ ONLY use information from the CONTEXT below - DO NOT use your general knowledge
2. ⚠️ If the context doesn't have the answer, say: "I couldn't find this information in your textbook."
3. ⚠️ DO NOT make up facts, dates, names, or examples that aren't in the context
4. ⚠️ If you're unsure, say so - don't guess or hallucinate

LANGUAGE LEVEL (Class {class_level}):
{language_instruction}

CONTEXT FROM TEXTBOOK:
{context}

STUDENT'S QUESTION:
{question}
"""
        
        mode_instructions = {
            "quick": f"""
MODE: QUICK/EXAM-STYLE (Class {class_level})
- Provide clear, direct answer
- Focus on key information from the textbook
- Well-structured with bullet points if explaining a topic
- If it's a simple question: 2-3 sentences
- If explaining a concept/topic: 1-2 paragraphs with key points
- Get straight to the point but cover the main aspects
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "define": f"""
MODE: DEFINE/MEANING (Class {class_level})
- Provide clear, concise definitions
- Explain key terms in simple language
- Give the meaning from the textbook context
- Use examples from context if available
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "elaborate": f"""
MODE: ELABORATE (Class {class_level})
- Provide detailed, comprehensive explanation
- Break down complex concepts step-by-step
- Include examples, applications, and connections
- Use bullet points or paragraphs as appropriate
- Make it thorough but easy to understand
- Language level: {language_complexity.get(class_level, "detailed but clear")}
""",
            "simple": f"""
MODE: SIMPLE EXPLANATION (Class {class_level})
- Break down complex ideas into simple parts
- Use analogies and comparisons from daily life
- Explain step-by-step if needed
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "meaning": f"""
MODE: MEANING/DEFINITION (Class {class_level})
- Define key terms in simple words
- Give the meaning from the textbook context
- Use examples from the context if available
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "story": f"""
MODE: STORY FORMAT (Class {class_level})
- Tell it like a story using ONLY facts from the context
- Make it interesting and memorable
- Use characters/events from the textbook
- Keep it factual - no made-up stories
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "example": f"""
MODE: EXAMPLES (Class {class_level})
- Give examples that are in the context/textbook
- If no examples in context, explain clearly: "The textbook doesn't give specific examples for this"
- Relate to student's real-life if possible (but only based on context info)
- Language level: {language_complexity.get(class_level, "simple and clear")}
""",
            "summary": f"""
MODE: SUMMARY (Class {class_level})
- Summarize the key points from the context
- Use bullet points or short paragraphs
- Cover main ideas only
- Keep it concise
- Language level: {language_complexity.get(class_level, "simple and clear")}
"""
        }
        
        return base_instruction + mode_instructions.get(mode, mode_instructions["elaborate"])
    
    def generate_mcqs(
        self, 
        context: str, 
        num_questions: int,
        class_level: int,
        subject: str,
        chapter: int,
        retry_count: int = 0
    ) -> list[dict]:
        """
        Generate concept-based MCQs using Gemini with automatic retry on 429 errors.
        
        Args:
            context: Full chapter/section text
            num_questions: Number of MCQs to generate
            class_level: Student's class (5-10)
            subject: Subject name
            chapter: Chapter number
            retry_count: Number of retries attempted (internal use)
        
        Returns:
            List of MCQ dictionaries
        """
        try:
            prompt = f"""You are creating MCQs for Class {class_level} students studying {subject}, Chapter {chapter}.

STRICT REQUIREMENTS:
1. Generate {num_questions} concept-based multiple-choice questions
2. DO NOT copy-paste sentences directly from the text
3. Test understanding and application, not memorization
4. Each question should have:
   - A clear question
   - 4 options (A, B, C, D)
   - Correct answer index (0-3)
   - Brief explanation of correct answer

CONTEXT FROM CHAPTER:
{context[:3000]}  

OUTPUT FORMAT (JSON):
[
  {{
    "question": "What is...?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "The answer is A because..."
  }},
  ...
]

Generate {num_questions} MCQs now in valid JSON format:"""
            
            # Get model with available API key
            model, key_index = self._get_model_with_available_key(retry_count)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            import json
            # Extract JSON from response (handle markdown code blocks)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            mcqs = json.loads(text.strip())
            return mcqs
        
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a 429 rate limit error
            if "429" in error_str and retry_count < len(gemini_key_manager.keys):
                logger.warning(f"⚠️  429 Rate limit hit. Rotating to next key (retry {retry_count + 1})...")
                
                # Force rotation to next key
                gemini_key_manager.current_key_index = (gemini_key_manager.current_key_index + 1) % len(gemini_key_manager.keys)
                
                # Retry with next key
                return self.generate_mcqs(context, num_questions, class_level, subject, chapter, retry_count + 1)
            
            logger.error(f"❌ MCQ generation failed: {e}")
            raise
    
    def evaluate_assessment(
        self,
        questions_and_answers: list[dict],
        class_level: int,
        subject: str,
        chapter: int,
        retry_count: int = 0
    ) -> dict:
        """
        Evaluate voice assessment answers using Gemini AI with automatic retry on 429 errors.
        
        Args:
            questions_and_answers: List of {"question": str, "answer": str}
            class_level: Student's class
            subject: Subject name
            chapter: Chapter number
            retry_count: Number of retries attempted (internal use)
        
        Returns:
            Evaluation result with score and feedback
        """
        try:
            qa_text = "\n\n".join([
                f"Q{i+1}: {qa['question']}\nA{i+1}: {qa['answer']}"
                for i, qa in enumerate(questions_and_answers)
            ])
            
            prompt = f"""You are evaluating a Class {class_level} student's answers for {subject}, Chapter {chapter}.

EVALUATION CRITERIA:
1. Accuracy (40%) - Is the answer factually correct?
2. Completeness (30%) - Does it cover key points?
3. Understanding (30%) - Does the student demonstrate comprehension?

STUDENT'S ANSWERS:
{qa_text}

PROVIDE:
1. Overall score (0-100)
2. Brief feedback (2-3 sentences)
3. List of strengths (2-3 points)
4. List of improvements needed (2-3 points)
5. Per-question scores (0-100 each)

OUTPUT FORMAT (JSON):
{{
  "score": 75,
  "feedback": "Overall feedback here...",
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "question_scores": [
    {{"question_num": 1, "score": 80, "note": "Brief note"}},
    ...
  ]
}}

Provide evaluation in JSON format:"""
            
            # Get model with available API key
            model, key_index = self._get_model_with_available_key(retry_count)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            import json
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            evaluation = json.loads(text.strip())
            return evaluation
        
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a 429 rate limit error
            if "429" in error_str and retry_count < len(gemini_key_manager.keys):
                logger.warning(f"⚠️  429 Rate limit hit. Rotating to next key (retry {retry_count + 1})...")
                
                # Force rotation to next key
                gemini_key_manager.current_key_index = (gemini_key_manager.current_key_index + 1) % len(gemini_key_manager.keys)
                
                # Retry with next key
                return self.evaluate_assessment(questions_and_answers, class_level, subject, chapter, retry_count + 1)
            
            logger.error(f"❌ Assessment evaluation failed: {e}")
            raise


# Global Gemini service instance
gemini_service = GeminiService()


