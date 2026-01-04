"""
Question Bank Service - Manages question generation and storage
Implements intelligent question caching and reuse
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.models.question_bank import QuestionSet, Question, StudentAssessmentAttempt
from app.services.rag_service import rag_service
from app.services.gemini_service import gemini_service
from app.db.mongo import mongodb
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QuestionBankService:
    """Service for managing question bank with MongoDB storage."""
    
    def __init__(self):
        self.question_sets_collection = "question_sets"
        self.attempts_collection = "assessment_attempts"
    
    def get_collection(self, collection_name: str):
        """Get MongoDB collection instance."""
        return mongodb.get_collection(collection_name)
    
    async def check_existing_questions(
        self,
        class_level: int,
        subject: str,
        chapter: int,
        page_range: str
    ) -> Optional[QuestionSet]:
        """
        Check if questions already exist for this page range.
        Returns existing QuestionSet if found, None otherwise.
        """
        try:
            collection = self.get_collection(self.question_sets_collection)
            
            # Search for existing question set
            query = {
                "class_level": class_level,
                "subject": subject,
                "chapter": chapter,
                "page_range": page_range
            }
            
            result = await collection.find_one(query)
            
            if result:
                logger.info(f"✅ Found existing questions for {subject} Ch.{chapter} pages {page_range}")
                # Increment usage count
                await collection.update_one(
                    {"_id": result["_id"]},
                    {"$inc": {"times_used": 1}}
                )
                return QuestionSet(**result)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking existing questions: {e}")
            return None
    
    async def generate_questions(
        self,
        class_level: int,
        subject: str,
        chapter: int,
        lesson_name: str,
        page_range: str,
        student_id: str
    ) -> QuestionSet:
        """
        Generate new question set using RAG + Gemini.
        Follows the specific distribution:
        - 5 Direct questions (2 easy, 2 medium, 1 hard)
        - 10 Concept questions (4 easy, 4 medium, 2 hard)
        """
        try:
            logger.info(f"📝 Generating NEW question set for {subject} Ch.{chapter} pages {page_range}")
            
            # Get content from the page range using RAG
            start_page, end_page = map(int, page_range.split('-'))
            context = rag_service.retrieve_chapter_context(
                class_level=class_level,
                subject=subject,
                chapter=chapter,
                max_chunks=20  # Get extensive context
            )
            
            # Generate Direct Questions (from textbook)
            direct_questions = await self._generate_direct_questions(
                context, class_level, page_range
            )
            
            # Generate Concept Questions (application-based)
            concept_questions = await self._generate_concept_questions(
                context, class_level, page_range
            )
            
            # Ensure page_range is set on each question
            for q in direct_questions:
                q.page_range = page_range
            for q in concept_questions:
                q.page_range = page_range

            # Create QuestionSet
            question_set = QuestionSet(
                class_level=class_level,
                subject=subject,
                chapter=chapter,
                lesson_name=lesson_name,
                page_range=page_range,
                direct_questions=direct_questions,
                concept_questions=concept_questions,
                generated_by=student_id,
                generated_at=datetime.utcnow(),
                times_used=1
            )
            
            # Save to MongoDB
            await self._save_question_set(question_set)
            
            logger.info(f"✅ Generated and saved question set with 15 questions")
            return question_set
            
        except Exception as e:
            logger.error(f"❌ Question generation error: {e}")
            raise
    
    async def _generate_direct_questions(
        self,
        context: str,
        class_level: int,
        page_range: str
    ) -> List[Question]:
        """Generate 5 direct questions from textbook (2 easy, 2 medium, 1 hard).

        Also request 3-6 expected KEYWORDS for each question to guide students and evaluation.
        """
        
        prompt = f"""You are creating DIRECT TEXTBOOK questions for Class {class_level} students.

**TEXTBOOK CONTENT (Pages {page_range}):**
{context}

**TASK:** Generate 5 DIRECT questions that ask EXACTLY what is written in the textbook.
These questions should have clear, specific answers from the text.

**DISTRIBUTION:**
1. Easy Question 1: Simple factual recall (What is X? Who is Y?)
2. Easy Question 2: Another simple factual question
3. Medium Question 1: Definition or explanation (Explain X. Describe Y.)
4. Medium Question 2: Compare or list (List the types of X. What are the features of Y?)
5. Hard Question 1: Detailed explanation requiring multiple facts from the text

**RULES:**
- Each question must be answerable from the provided textbook content
- Questions should be direct and specific
- Avoid questions requiring outside knowledge
- Use age-appropriate language for Class {class_level}

**FORMAT (STRICT):**
Return EXACTLY 5 lines, each on a new line with label and keywords:
[EASY 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)
[EASY 2] Question text (KEYWORDS: keyword1, keyword2, keyword3)
[MEDIUM 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)
[MEDIUM 2] Question text (KEYWORDS: keyword1, keyword2, keyword3)
[HARD 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)
"""

        response = gemini_service.generate_response(prompt)
        return self._parse_questions(response, "direct")
    
    async def _generate_concept_questions(
        self,
        context: str,
        class_level: int,
        page_range: str
    ) -> List[Question]:
        """Generate 10 concept/application questions (4 easy, 4 medium, 2 hard).

        Also request 3-6 expected KEYWORDS for each question to guide students and evaluation.
        """

        prompt = (
            f"You are creating CONCEPT & APPLICATION questions for Class {class_level} students.\n\n"
            f"TEXTBOOK CONTENT (Pages {page_range}):\n{context}\n\n"
            "TASK: Generate 10 CONCEPT-BASED questions that test understanding and application. "
            "These questions require students to think, connect ideas, and apply concepts.\n\n"
            "DISTRIBUTION:\n1-4. Easy Concept Questions (4): Why questions, cause-effect, simple connections\n"
            "5-8. Medium Concept Questions (4): How questions, application, real-world examples\n"
            "9-10. Hard Concept Questions (2): Analysis, evaluation, deep understanding\n\n"
            "RULES:\n- Questions must be based on textbook concepts but require thinking\n"
            "- Test understanding, not just memorization\n- Encourage explanation and reasoning\n"
            f"- Appropriate for Class {class_level} cognitive level\n\n"
            "FORMAT (STRICT): Return EXACTLY 10 lines, each on a new line with label and keywords:\n"
            "[EASY 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[EASY 2] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[EASY 3] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[EASY 4] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[MEDIUM 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[MEDIUM 2] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[MEDIUM 3] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[MEDIUM 4] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[HARD 1] Question text (KEYWORDS: keyword1, keyword2, keyword3)\n"
            "[HARD 2] Question text (KEYWORDS: keyword1, keyword2, keyword3)"
        )

        # Call Gemini to generate concept questions
        response = gemini_service.generate_response(prompt)
        return self._parse_questions(response, "concept")
    
    def _parse_questions(self, response: str, question_type: str) -> List[Question]:
        """Parse Gemini response into Question objects."""
        questions = []
        
        for line in response.split('\n'):
            line = line.strip()
            if not line or not line.startswith('['):
                continue
            
            try:
                # Extract difficulty and question
                if '[EASY' in line:
                    difficulty = "easy"
                elif '[MEDIUM' in line:
                    difficulty = "medium"
                elif '[HARD' in line:
                    difficulty = "hard"
                else:
                    continue
                
                # Extract question text and optional keywords in format (KEYWORDS: a, b, c)
                content = line.split(']', 1)[1].strip()
                question_text = content
                keywords: List[str] = []
                upper = content.upper()
                if '(KEYWORDS:' in upper:
                    idx = upper.rfind('(KEYWORDS:')
                    q_part = content[:idx].strip()
                    kw_part = content[idx:]
                    if ')' in kw_part:
                        raw = kw_part.split(':', 1)[1].split(')', 1)[0]
                        keywords = [k.strip() for k in raw.split(',') if k.strip()]
                    question_text = q_part.rstrip('-: ').strip()
                
                if question_text and len(question_text) > 10:
                    questions.append(Question(
                        question_text=question_text,
                        question_type=question_type,
                        difficulty=difficulty,
                        page_range="",  # Will be set by caller
                        expected_keywords=keywords,
                        sample_answer=None
                    ))
            except Exception as e:
                logger.warning(f"⚠️ Could not parse question line: {line} - {e}")
                continue
        
        return questions
    
    async def _save_question_set(self, question_set: QuestionSet):
        """Save question set to MongoDB."""
        try:
            collection = self.get_collection(self.question_sets_collection)
            
            # Convert to dict and save
            data = question_set.dict()
            result = await collection.insert_one(data)
            
            logger.info(f"✅ Saved question set with ID: {result.inserted_id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving question set: {e}")
            raise
    
    async def save_assessment_attempt(
        self,
        student_id: str,
        question_set_id: str,
        answers: List[dict],
        evaluation: dict
    ):
        """Save student's assessment attempt."""
        try:
            collection = self.get_collection(self.attempts_collection)
            
            attempt = {
                "student_id": student_id,
                "question_set_id": question_set_id,
                "answers": answers,
                "total_score": evaluation.get("score", 0),
                "feedback": evaluation.get("feedback", ""),
                "strengths": evaluation.get("strengths", []),
                "improvements": evaluation.get("improvements", []),
                "topics_to_study": evaluation.get("topics_to_study", []),
                "completed_at": datetime.utcnow()
            }
            
            result = await collection.insert_one(attempt)
            logger.info(f"✅ Saved assessment attempt with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error saving assessment attempt: {e}")
            raise


# Global instance
question_bank_service = QuestionBankService()
