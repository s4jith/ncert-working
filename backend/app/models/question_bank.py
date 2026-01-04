"""
Question Bank Models for MongoDB Storage
Stores generated questions for reuse across students
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class Question(BaseModel):
    """Single question with metadata."""
    question_text: str = Field(..., description="The actual question")
    question_type: Literal["direct", "concept"] = Field(..., description="Direct from book or concept-based")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty level")
    page_range: str = Field(..., description="Page range (e.g., '1-10')")
    expected_keywords: List[str] = Field(default=[], description="Keywords for evaluation")
    sample_answer: Optional[str] = Field(None, description="Sample answer for reference")


class QuestionSet(BaseModel):
    """Complete question set for a 10-page segment."""
    class_level: int = Field(..., ge=5, le=10)
    subject: str = Field(...)
    chapter: int = Field(..., ge=1)
    lesson_name: str = Field(...)
    page_range: str = Field(..., description="e.g., '1-10', '11-20'")
    
    # 5 Direct questions (2 easy, 2 medium, 1 hard)
    direct_questions: List[Question] = Field(..., min_length=5, max_length=5)
    
    # 10 Concept questions (4 easy, 4 medium, 2 hard)
    concept_questions: List[Question] = Field(..., min_length=10, max_length=10)
    
    # Metadata
    generated_by: str = Field(..., description="Student ID who first generated this set")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    times_used: int = Field(default=0, description="Number of times reused")
    average_score: Optional[float] = Field(None, description="Average score across all attempts")


class StudentAssessmentAttempt(BaseModel):
    """Individual student's attempt at a question set."""
    student_id: str = Field(...)
    question_set_id: str = Field(..., description="Reference to QuestionSet")
    class_level: int = Field(...)
    subject: str = Field(...)
    chapter: int = Field(...)
    page_range: str = Field(...)
    
    # Answers
    answers: List[dict] = Field(..., description="List of {question_text, student_answer, score}")
    
    # Results
    total_score: float = Field(..., ge=0, le=100)
    correct_answers: int = Field(...)
    feedback: str = Field(...)
    strengths: List[str] = Field(...)
    improvements: List[str] = Field(...)
    topics_to_study: List[str] = Field(...)
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    time_taken_seconds: int = Field(...)


class QuestionGenerationRequest(BaseModel):
    """Request for generating new question set."""
    class_level: int = Field(..., ge=5, le=10)
    subject: str = Field(...)
    chapter: int = Field(..., ge=1)
    lesson_name: str = Field(...)
    page_range: str = Field(..., description="e.g., '1-10'")
    student_id: str = Field(..., description="Student requesting generation")
    force_regenerate: bool = Field(default=False, description="Force new generation even if exists")


class QuestionRetrievalRequest(BaseModel):
    """Request for retrieving existing question set."""
    class_level: int = Field(..., ge=5, le=10)
    subject: str = Field(...)
    chapter: int = Field(..., ge=1)
    page_range: str = Field(...)
