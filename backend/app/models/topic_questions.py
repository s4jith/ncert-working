"""
Topic-based Question Bank Models for MongoDB Storage
Stores pre-generated questions organized by subject/chapter/topic for reuse across all students
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict
from datetime import datetime
from bson import ObjectId


class TopicQuestion(BaseModel):
    """Single question with metadata for a specific topic."""
    question_id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique question ID")
    question_text: str = Field(..., description="The actual question")
    question_type: Literal["conceptual", "application", "recall", "analytical"] = Field(
        ..., description="Type of question"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty level")
    expected_answer: Optional[str] = Field(None, description="Expected answer for evaluation")
    keywords: List[str] = Field(default=[], description="Keywords for answer evaluation")
    marks: int = Field(default=5, description="Marks for this question")
    time_estimate_seconds: int = Field(default=60, description="Estimated time to answer")
    source_page: Optional[int] = Field(None, description="Source page in textbook")
    
    class Config:
        json_encoders = {ObjectId: str}


class Topic(BaseModel):
    """A topic within a chapter with its questions."""
    topic_id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique topic ID")
    topic_name: str = Field(..., description="Name of the topic")
    topic_description: Optional[str] = Field(None, description="Brief description")
    page_range: str = Field(..., description="Page range in textbook (e.g., '1-5')")
    
    # Questions for this topic
    questions: List[TopicQuestion] = Field(default=[], description="All questions for this topic")
    
    # Stats
    total_questions: int = Field(default=0, description="Total number of questions")
    difficulty_distribution: Dict[str, int] = Field(
        default={"easy": 0, "medium": 0, "hard": 0},
        description="Count of questions by difficulty"
    )
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {ObjectId: str}


class ChapterQuestionBank(BaseModel):
    """Complete question bank for a chapter with all topics."""
    class_level: int = Field(..., ge=5, le=12, description="Class level")
    subject: str = Field(..., description="Subject name")
    chapter_number: int = Field(..., ge=1, description="Chapter number")
    chapter_name: str = Field(..., description="Chapter name")
    
    # Topics with questions
    topics: List[Topic] = Field(default=[], description="All topics in this chapter")
    
    # Summary stats
    total_topics: int = Field(default=0)
    total_questions: int = Field(default=0)
    
    # Metadata
    source_pdf: Optional[str] = Field(None, description="Source PDF filename")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True, description="Whether this bank is active")
    
    class Config:
        json_encoders = {ObjectId: str}


class StudentTopicPerformance(BaseModel):
    """Track student performance on a specific topic."""
    student_id: str = Field(..., description="Student ID")
    class_level: int = Field(...)
    subject: str = Field(...)
    chapter_number: int = Field(...)
    topic_id: str = Field(...)
    topic_name: str = Field(...)
    
    # Performance metrics
    tests_taken: int = Field(default=0)
    total_questions_attempted: int = Field(default=0)
    correct_answers: int = Field(default=0)
    average_score: float = Field(default=0.0)
    best_score: float = Field(default=0.0)
    latest_score: float = Field(default=0.0)
    
    # Trend
    score_history: List[Dict] = Field(default=[], description="List of {score, date}")
    improvement_trend: Literal["improving", "declining", "stable"] = Field(default="stable")
    
    # Metadata
    first_attempted: Optional[datetime] = None
    last_attempted: Optional[datetime] = None
    
    class Config:
        json_encoders = {ObjectId: str}


class StudentSubjectProgress(BaseModel):
    """Overall progress of a student in a subject."""
    student_id: str = Field(...)
    class_level: int = Field(...)
    subject: str = Field(...)
    
    # Chapters completed
    chapters_attempted: List[int] = Field(default=[])
    chapters_mastered: List[int] = Field(default=[], description="Chapters with avg score > 80%")
    
    # Topic performance summary
    total_topics: int = Field(default=0)
    topics_strong: int = Field(default=0, description="Topics with score >= 80%")
    topics_moderate: int = Field(default=0, description="Topics with score 60-80%")
    topics_weak: int = Field(default=0, description="Topics with score < 60%")
    
    # Weak areas for recommendations
    weak_topics: List[Dict] = Field(
        default=[], 
        description="List of {topic_id, topic_name, chapter, score}"
    )
    
    # Overall stats
    overall_average: float = Field(default=0.0)
    total_tests_taken: int = Field(default=0)
    total_study_time_minutes: int = Field(default=0)
    
    # Metadata
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {ObjectId: str}


class TestSession(BaseModel):
    """A test session taken by a student."""
    session_id: str = Field(default_factory=lambda: str(ObjectId()))
    student_id: str = Field(...)
    class_level: int = Field(...)
    subject: str = Field(...)
    chapter_number: int = Field(...)
    topic_id: str = Field(...)
    topic_name: str = Field(...)
    
    # Test configuration
    num_questions: int = Field(default=5)
    time_limit_minutes: int = Field(default=10)
    difficulty_preference: Optional[str] = Field(None, description="easy/medium/hard/mixed")
    
    # Questions served (from question bank)
    questions_served: List[Dict] = Field(
        default=[], 
        description="List of {question_id, question_text, difficulty}"
    )
    
    # Answers submitted
    answers: List[Dict] = Field(
        default=[], 
        description="List of {question_id, answer_text, submitted_at}"
    )
    
    # Evaluation results
    score: Optional[float] = None
    correct_count: int = Field(default=0)
    evaluation_details: List[Dict] = Field(
        default=[], 
        description="List of {question_id, is_correct, feedback, score}"
    )
    
    # Feedback
    overall_feedback: Optional[str] = None
    topics_to_review: List[str] = Field(default=[])
    
    # Status & timing
    status: Literal["started", "in_progress", "completed", "abandoned"] = Field(default="started")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    
    class Config:
        json_encoders = {ObjectId: str}


class SubjectInfo(BaseModel):
    """Subject information available for a student."""
    subject: str = Field(...)
    class_level: int = Field(...)
    total_chapters: int = Field(default=0)
    chapters: List[Dict] = Field(
        default=[], 
        description="List of {chapter_number, chapter_name, topic_count}"
    )
    is_available: bool = Field(default=True)
    
    class Config:
        json_encoders = {ObjectId: str}
