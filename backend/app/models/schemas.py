"""
Pydantic models/schemas for request and response validation.
All API endpoints use these schemas for type safety and validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ==================== CHAT / RAG SCHEMAS ====================

class ChatRequest(BaseModel):
    """Request schema for RAG-based chat."""
    class_level: int = Field(..., ge=5, le=10, description="Class level (5-10)")
    subject: str = Field(..., description="Subject name (e.g., Geography, History)")
    chapter: int = Field(..., ge=1, description="Chapter number")
    highlight_text: str = Field(..., min_length=1, description="Text highlighted by student")
    mode: Literal["define", "elaborate", "simple", "meaning", "story", "example", "summary"] = Field(
        ..., description="Explanation mode requested by student"
    )


class ChatResponse(BaseModel):
    """Response schema for RAG-based chat."""
    answer: str = Field(..., description="Gemini-formatted answer using RAG context")
    used_mode: str = Field(..., description="Mode used for explanation")
    source_chunks: List[str] = Field(..., description="RAG chunks used for context")


# ==================== MCQ SCHEMAS ====================

class MCQ(BaseModel):
    """Single MCQ question structure."""
    question: str = Field(..., description="MCQ question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Four options")
    correct_index: int = Field(..., ge=0, le=3, description="Index of correct answer (0-3)")
    explanation: str = Field(..., description="Explanation of correct answer")


class MCQGenerationRequest(BaseModel):
    """Request schema for generating MCQs."""
    class_level: int = Field(..., ge=5, le=12, description="Class level (5-12)")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")
    num_questions: int = Field(5, ge=1, le=20, description="Number of MCQs to generate")
    page_range: Optional[tuple[int, int]] = Field(None, description="Optional page range (start, end)")
    use_local_model: bool = Field(False, description="Use Intel OpenVINO local model for generation")


class MCQGenerationResponse(BaseModel):
    """Response schema for MCQ generation."""
    mcqs: List[MCQ] = Field(..., description="Generated MCQs")
    metadata: dict = Field(..., description="Generation metadata (class, subject, chapter)")
    used_pipeline: str = Field("gemini", description="Pipeline used: gemini, openvino, or openvino-hybrid")
    inference_time_ms: Optional[float] = Field(None, description="Inference time in milliseconds")


# ==================== EVALUATION SCHEMAS ====================

class MCQAnswer(BaseModel):
    """Student's answer to an MCQ."""
    question_index: int = Field(..., description="Index of the question answered")
    selected_index: int = Field(..., ge=0, le=3, description="Selected answer index (0-3)")


class EvaluationRequest(BaseModel):
    """Request schema for evaluating MCQ answers."""
    student_id: Optional[str] = Field(None, description="Student identifier (optional)")
    class_level: int = Field(..., ge=5, le=10, description="Class level")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")
    mcqs: List[MCQ] = Field(..., description="Original MCQs")
    answers: List[MCQAnswer] = Field(..., description="Student's answers")


class EvaluationResult(BaseModel):
    """Detailed evaluation result."""
    total_questions: int = Field(..., description="Total number of questions")
    correct_answers: int = Field(..., description="Number of correct answers")
    percentage: float = Field(..., description="Percentage score")
    feedback: str = Field(..., description="AI-generated feedback")
    question_results: List[dict] = Field(..., description="Per-question results")


class EvaluationResponse(BaseModel):
    """Response schema for evaluation."""
    result: EvaluationResult = Field(..., description="Evaluation result")
    saved_to_db: bool = Field(..., description="Whether result was saved to MongoDB")
    evaluation_id: Optional[str] = Field(None, description="MongoDB document ID")


# ==================== NOTES SCHEMAS ====================

class NoteCreateRequest(BaseModel):
    """Request schema for creating a note."""
    student_id: str = Field(..., description="Student identifier")
    class_level: int = Field(..., ge=5, le=10, description="Class level")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")
    page_number: int = Field(..., ge=1, description="Page number where note was created")
    highlight_text: str = Field(..., description="Highlighted text")
    note_content: str = Field(..., description="Note content")
    heading: Optional[str] = Field(None, description="Optional note heading")


class Note(BaseModel):
    """Note model with metadata."""
    id: str = Field(..., description="MongoDB _id")
    student_id: str
    class_level: int
    subject: str
    chapter: int
    page_number: int
    highlight_text: str
    note_content: str
    heading: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class NotesListResponse(BaseModel):
    """Response schema for listing notes."""
    notes: List[Note] = Field(..., description="List of notes")
    total: int = Field(..., description="Total number of notes")


# ==================== ASSESSMENT SCHEMAS (VOICE) ====================

class AssessmentAnswer(BaseModel):
    """Single answer in voice assessment."""
    question: str = Field(..., description="Question asked")
    answer: str = Field(..., description="Student's transcribed answer")
    timestamp: float = Field(..., description="Timestamp in video/audio")


class AssessmentSubmitRequest(BaseModel):
    """Request schema for submitting assessment."""
    student_id: str = Field(..., description="Student identifier")
    class_level: int = Field(..., ge=5, le=10, description="Class level")
    subject: str = Field(..., description="Subject name")
    chapter: int = Field(..., ge=1, description="Chapter number")
    answers: List[AssessmentAnswer] = Field(..., description="List of Q&A pairs")


class AssessmentResult(BaseModel):
    """Assessment evaluation result."""
    score: float = Field(..., ge=0, le=100, description="Overall score (0-100)")
    feedback: str = Field(..., description="AI-generated feedback")
    strengths: List[str] = Field(..., description="Student's strengths")
    improvements: List[str] = Field(..., description="Areas for improvement")
    question_scores: List[dict] = Field(..., description="Per-question scores")


class AssessmentResponse(BaseModel):
    """Response schema for assessment submission."""
    result: AssessmentResult = Field(..., description="Assessment result")
    assessment_id: str = Field(..., description="MongoDB document ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== GENERIC RESPONSE ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Optional response data")
