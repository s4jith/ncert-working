"""
RAG-based Evaluation Service
Evaluates student answers using Pinecone context retrieval and Gemini.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging
import json
import re

from app.db.mongo import mongodb
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.services.topic_question_bank_service import topic_question_bank_service

logger = logging.getLogger(__name__)


class RAGEvaluationService:
    """
    Service for evaluating student answers using RAG.
    
    Process:
    1. Retrieve relevant context from Pinecone for each question
    2. Use Gemini to evaluate answer against context
    3. Generate feedback and identify weak areas
    4. Update student performance tracking
    """
    
    SESSIONS_COLLECTION = "test_sessions"
    
    async def evaluate_test_session(
        self,
        session_id: str,
        student_id: str,
        class_level: int,
        subject: str,
        chapter_number: int,
        topic_id: str,
        topic_name: str,
        questions: List[Dict],
        answers: List[Dict]
    ) -> Dict:
        """
        Evaluate a complete test session.
        
        Args:
            session_id: Test session ID
            student_id: Student ID
            class_level: Class level (5-12)
            subject: Subject name
            chapter_number: Chapter number
            topic_id: Topic ID
            topic_name: Topic name
            questions: List of questions served
            answers: List of student answers
        
        Returns:
            Evaluation result with scores, feedback, and recommendations
        """
        logger.info(f"📊 Evaluating test session {session_id} for student {student_id}")
        
        # Build Q&A pairs
        qa_pairs = self._build_qa_pairs(questions, answers)
        
        if not qa_pairs:
            return self._empty_result(session_id)
        
        # Retrieve context from Pinecone for this topic
        context = await self._get_topic_context(class_level, subject, chapter_number, topic_name)
        
        # Evaluate each answer
        evaluations = []
        total_score = 0
        correct_count = 0
        max_possible = 0
        
        for qa in qa_pairs:
            eval_result = await self._evaluate_single_answer(
                question=qa["question"],
                answer=qa["answer"],
                expected_answer=qa.get("expected_answer"),
                keywords=qa.get("keywords", []),
                context=context,
                class_level=class_level,
                subject=subject
            )
            
            evaluations.append({
                "question_id": qa["question_id"],
                "question_text": qa["question"],
                "student_answer": qa["answer"],
                "is_correct": eval_result["is_correct"],
                "score": eval_result["score"],
                "max_score": qa.get("marks", 10),
                "feedback": eval_result["feedback"],
                "correct_answer": eval_result.get("correct_answer", "")
            })
            
            total_score += eval_result["score"]
            max_possible += qa.get("marks", 10)
            if eval_result["is_correct"]:
                correct_count += 1
        
        # Calculate percentage score
        percentage_score = round((total_score / max_possible) * 100, 1) if max_possible > 0 else 0
        
        # Generate overall feedback
        overall_feedback = await self._generate_overall_feedback(
            evaluations=evaluations,
            percentage_score=percentage_score,
            correct_count=correct_count,
            total_questions=len(questions),
            topic_name=topic_name,
            context=context
        )
        
        # Identify weak areas
        weak_areas = self._identify_weak_areas(evaluations)
        
        # Update student performance
        await topic_question_bank_service.update_student_performance(
            student_id=student_id,
            class_level=class_level,
            subject=subject,
            chapter_number=chapter_number,
            topic_id=topic_id,
            topic_name=topic_name,
            score=percentage_score,
            questions_attempted=len(questions),
            correct_count=correct_count
        )
        
        # Save session results
        await self._save_session_results(
            session_id=session_id,
            student_id=student_id,
            score=percentage_score,
            evaluations=evaluations,
            overall_feedback=overall_feedback,
            weak_areas=weak_areas
        )
        
        logger.info(f"✅ Evaluation complete: {percentage_score}% ({correct_count}/{len(questions)} correct)")
        
        return {
            "session_id": session_id,
            "score": percentage_score,
            "total_questions": len(questions),
            "correct_answers": correct_count,
            "evaluations": evaluations,
            "feedback": overall_feedback["summary"],
            "strengths": overall_feedback["strengths"],
            "improvements": overall_feedback["improvements"],
            "topics_to_review": weak_areas,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def _build_qa_pairs(self, questions: List[Dict], answers: List[Dict]) -> List[Dict]:
        """Match questions with answers."""
        answer_map = {a.get("question_id") or a.get("question_number"): a.get("answer", "") for a in answers}
        
        pairs = []
        for q in questions:
            q_id = q.get("question_id") or q.get("question_number")
            pairs.append({
                "question_id": q_id,
                "question": q.get("question_text", ""),
                "answer": answer_map.get(q_id, ""),
                "expected_answer": q.get("expected_answer"),
                "keywords": q.get("keywords", []),
                "marks": q.get("marks", 10),
                "difficulty": q.get("difficulty", "medium")
            })
        
        return pairs
    
    async def _get_topic_context(
        self,
        class_level: int,
        subject: str,
        chapter_number: int,
        topic_name: str
    ) -> str:
        """Retrieve relevant context from Pinecone for the topic."""
        try:
            query = f"{topic_name} {subject} class {class_level} chapter {chapter_number}"
            
            context_docs = await rag_service.get_relevant_context(
                query=query,
                class_level=class_level,
                subject=subject,
                top_k=15
            )
            
            context = "\n\n".join([doc.get("text", "") for doc in context_docs])
            logger.info(f"Retrieved {len(context_docs)} context chunks for evaluation")
            
            return context[:20000]  # Limit context size
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    async def _evaluate_single_answer(
        self,
        question: str,
        answer: str,
        expected_answer: Optional[str],
        keywords: List[str],
        context: str,
        class_level: int,
        subject: str
    ) -> Dict:
        """Evaluate a single student answer."""
        
        if not answer or not answer.strip():
            return {
                "is_correct": False,
                "score": 0,
                "feedback": "No answer provided.",
                "correct_answer": expected_answer or "Please refer to the textbook."
            }
        
        prompt = f"""You are evaluating a Class {class_level} {subject} student's answer.

**QUESTION:** {question}

**STUDENT'S ANSWER:** {answer}

**EXPECTED ANSWER (Reference):** {expected_answer or "Not provided"}

**KEY CONCEPTS/KEYWORDS:** {', '.join(keywords) if keywords else "Not specified"}

**TEXTBOOK CONTEXT:**
{context[:5000]}

**EVALUATION TASK:**
1. Check if the student's answer is correct based on the textbook content
2. Identify key points covered and missed
3. Assign a score out of 10
4. Provide constructive feedback

**OUTPUT FORMAT (JSON):**
{{
    "is_correct": true/false (true if score >= 6),
    "score": number (0-10),
    "feedback": "Constructive feedback for the student",
    "correct_answer": "The correct/complete answer from textbook"
}}

Be fair but encouraging. Consider partial credit for partially correct answers.
Output ONLY the JSON."""

        try:
            response = await gemini_service.generate_text(prompt)
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "is_correct": result.get("is_correct", False),
                    "score": min(10, max(0, result.get("score", 0))),
                    "feedback": result.get("feedback", ""),
                    "correct_answer": result.get("correct_answer", "")
                }
            
            # Fallback if JSON parsing fails
            return {
                "is_correct": False,
                "score": 5,
                "feedback": "Your answer has been recorded. Please review the textbook for the complete answer.",
                "correct_answer": expected_answer or ""
            }
            
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {
                "is_correct": False,
                "score": 5,
                "feedback": "Could not fully evaluate. Please review your answer.",
                "correct_answer": expected_answer or ""
            }
    
    async def _generate_overall_feedback(
        self,
        evaluations: List[Dict],
        percentage_score: float,
        correct_count: int,
        total_questions: int,
        topic_name: str,
        context: str
    ) -> Dict:
        """Generate overall feedback for the test."""
        
        # Analyze evaluations
        correct_answers = [e for e in evaluations if e["is_correct"]]
        incorrect_answers = [e for e in evaluations if not e["is_correct"]]
        
        prompt = f"""Generate overall feedback for a student's test on "{topic_name}".

**PERFORMANCE:**
- Score: {percentage_score}%
- Correct: {correct_count}/{total_questions}

**CORRECT ANSWERS:**
{[e["question_text"][:100] for e in correct_answers]}

**INCORRECT ANSWERS:**
{[{"q": e["question_text"][:100], "feedback": e["feedback"]} for e in incorrect_answers]}

**TASK:** Generate:
1. A brief summary (2-3 sentences)
2. 2-3 strengths shown
3. 2-3 areas for improvement
4. Encouragement message

**OUTPUT FORMAT (JSON):**
{{
    "summary": "Overall feedback summary...",
    "strengths": ["strength 1", "strength 2"],
    "improvements": ["area 1", "area 2"],
    "encouragement": "Keep up the good work!"
}}

Be encouraging and constructive. Output ONLY the JSON."""

        try:
            response = await gemini_service.generate_text(prompt)
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
        except Exception as e:
            logger.error(f"Feedback generation error: {e}")
        
        # Fallback feedback
        if percentage_score >= 80:
            return {
                "summary": f"Excellent performance on {topic_name}! You demonstrated strong understanding.",
                "strengths": ["Good conceptual understanding", "Clear explanations"],
                "improvements": ["Continue practicing to maintain performance"],
                "encouragement": "Outstanding work! Keep it up!"
            }
        elif percentage_score >= 60:
            return {
                "summary": f"Good effort on {topic_name}. You understand the basics but can improve.",
                "strengths": ["Basic understanding present", "Attempted all questions"],
                "improvements": ["Review incorrect answers", "Practice more problems"],
                "encouragement": "You're on the right track! Keep practicing!"
            }
        else:
            return {
                "summary": f"Keep practicing {topic_name}. Review the textbook and try again.",
                "strengths": ["Showed effort", "Attempted the test"],
                "improvements": ["Review basic concepts", "Study the textbook more", "Ask for help if needed"],
                "encouragement": "Don't give up! Learning takes time. You'll improve with practice!"
            }
    
    def _identify_weak_areas(self, evaluations: List[Dict]) -> List[str]:
        """Identify topics/areas where student needs improvement."""
        weak_areas = []
        
        for e in evaluations:
            if not e["is_correct"] and e["score"] < 5:
                # Extract topic from question
                q = e["question_text"].lower()
                if "what is" in q or "define" in q:
                    weak_areas.append("Basic definitions and concepts")
                elif "explain" in q or "describe" in q:
                    weak_areas.append("Detailed explanations")
                elif "compare" in q or "difference" in q:
                    weak_areas.append("Comparisons and distinctions")
                elif "why" in q or "how" in q:
                    weak_areas.append("Reasoning and understanding")
                elif "example" in q or "application" in q:
                    weak_areas.append("Practical applications")
                else:
                    weak_areas.append("General understanding")
        
        # Deduplicate
        return list(set(weak_areas))[:5]
    
    async def _save_session_results(
        self,
        session_id: str,
        student_id: str,
        score: float,
        evaluations: List[Dict],
        overall_feedback: Dict,
        weak_areas: List[str]
    ):
        """Save test session results to MongoDB."""
        collection = mongodb.db[self.SESSIONS_COLLECTION]
        
        await collection.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": "completed",
                "score": score,
                "evaluation_details": evaluations,
                "overall_feedback": overall_feedback,
                "topics_to_review": weak_areas,
                "completed_at": datetime.utcnow()
            }}
        )
    
    def _empty_result(self, session_id: str) -> Dict:
        """Return empty result for failed evaluation."""
        return {
            "session_id": session_id,
            "score": 0,
            "total_questions": 0,
            "correct_answers": 0,
            "evaluations": [],
            "feedback": "No answers to evaluate.",
            "strengths": [],
            "improvements": ["Please answer the questions"],
            "topics_to_review": [],
            "completed_at": datetime.utcnow().isoformat()
        }


# Global instance
rag_evaluation_service = RAGEvaluationService()
