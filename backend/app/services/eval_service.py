"""
Evaluation Service - Handles MCQ evaluation and scoring.
"""

from app.db.mongo import get_evaluations_collection
from app.models.schemas import MCQ, MCQAnswer, EvaluationResult
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating student answers and saving results."""
    
    async def evaluate_mcqs(
        self,
        student_id: str,
        class_level: int,
        subject: str,
        chapter: int,
        mcqs: list[MCQ],
        answers: list[MCQAnswer]
    ) -> tuple[EvaluationResult, str]:
        """
        Evaluate student's MCQ answers.
        
        Args:
            student_id: Student identifier
            class_level: Class (5-10)
            subject: Subject name
            chapter: Chapter number
            mcqs: Original MCQ questions
            answers: Student's answers
        
        Returns:
            Tuple of (EvaluationResult, evaluation_id)
        """
        try:
            # Step 1: Calculate scores
            total = len(mcqs)
            correct = 0
            question_results = []
            
            for answer in answers:
                idx = answer.question_index
                if idx < 0 or idx >= len(mcqs):
                    continue
                
                mcq = mcqs[idx]
                is_correct = answer.selected_index == mcq.correct_index
                
                if is_correct:
                    correct += 1
                
                question_results.append({
                    "question_index": idx,
                    "question": mcq.question,
                    "selected_option": mcq.options[answer.selected_index],
                    "correct_option": mcq.options[mcq.correct_index],
                    "is_correct": is_correct,
                    "explanation": mcq.explanation
                })
            
            percentage = (correct / total * 100) if total > 0 else 0
            
            # Step 2: Generate feedback
            feedback = self._generate_feedback(correct, total, percentage)
            
            # Step 3: Create evaluation result
            result = EvaluationResult(
                total_questions=total,
                correct_answers=correct,
                percentage=round(percentage, 2),
                feedback=feedback,
                question_results=question_results
            )
            
            # Step 4: Save to MongoDB
            evaluation_id = await self._save_evaluation(
                student_id=student_id,
                class_level=class_level,
                subject=subject,
                chapter=chapter,
                result=result
            )
            
            logger.info(f"✅ Evaluation completed: {correct}/{total} ({percentage:.1f}%)")
            return result, evaluation_id
        
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            raise
    
    def _generate_feedback(self, correct: int, total: int, percentage: float) -> str:
        """Generate personalized feedback based on score."""
        if percentage >= 90:
            return f"Excellent work! You scored {correct}/{total} ({percentage:.1f}%). You have a strong understanding of this chapter. Keep it up!"
        elif percentage >= 70:
            return f"Good job! You scored {correct}/{total} ({percentage:.1f}%). You understand most concepts well. Review the incorrect answers to strengthen your knowledge."
        elif percentage >= 50:
            return f"Fair attempt. You scored {correct}/{total} ({percentage:.1f}%). There's room for improvement. Focus on understanding the concepts better by reviewing the chapter."
        else:
            return f"You scored {correct}/{total} ({percentage:.1f}%). Don't worry! This is a learning opportunity. Review the chapter carefully and try again. You can do it!"
    
    async def _save_evaluation(
        self,
        student_id: str,
        class_level: int,
        subject: str,
        chapter: int,
        result: EvaluationResult
    ) -> str:
        """Save evaluation result to MongoDB."""
        try:
            collection = get_evaluations_collection()
            
            document = {
                "student_id": student_id,
                "class_level": class_level,
                "subject": subject,
                "chapter": chapter,
                "total_questions": result.total_questions,
                "correct_answers": result.correct_answers,
                "percentage": result.percentage,
                "feedback": result.feedback,
                "question_results": result.question_results,
                "created_at": datetime.utcnow()
            }
            
            result_doc = await collection.insert_one(document)
            return str(result_doc.inserted_id)
        
        except Exception as e:
            logger.error(f"❌ Failed to save evaluation: {e}")
            raise


# Global evaluation service instance
eval_service = EvaluationService()
