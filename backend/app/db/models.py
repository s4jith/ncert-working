"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    LOCAL = "local"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SourceType(str, Enum):
    NCERT_TEXTBOOK = "ncert_textbook"
    WEB = "web"
    AI_GENERATED = "ai_generated"


# ==================== AUTH MODELS ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    grade: Optional[int] = Field(None, ge=5, le=12)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    grade: Optional[int]
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


# ==================== CHAT MODELS ====================

class ChatSource(BaseModel):
    """Source/citation for RAG response"""
    type: SourceType
    name: str
    class_num: Optional[str] = Field(None, alias="class")
    subject: Optional[str] = None
    chapter: Optional[str] = None
    page: Optional[int] = None
    relevance: Optional[str] = None
    url: Optional[str] = None
    
    class Config:
        populate_by_name = True


class ChatMessage(BaseModel):
    """Single chat message"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: Optional[List[ChatSource]] = None
    images: Optional[List[str]] = None


class ChatRequest(BaseModel):
    """Chat request from user"""
    message: str = Field(..., min_length=1, max_length=5000)
    model: LLMProvider = LLMProvider.GEMINI
    grade: Optional[int] = Field(None, ge=5, le=12, description="Grade level for filtering")
    subject: Optional[str] = None
    language: Optional[str] = Field("en", description="Preferred response language")
    include_images: bool = False
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response from AI"""
    message: str
    sources: List[ChatSource] = []
    images: List[str] = []
    model_used: LLMProvider
    language_detected: str
    response_time_ms: int
    cached: bool = False
    conversation_id: str
    citation_count: int = 0


class ChatHistoryResponse(BaseModel):
    """Paginated chat history"""
    messages: List[ChatMessage]
    total: int
    page: int
    per_page: int


# ==================== QUIZ MODELS ====================

class QuizQuestion(BaseModel):
    """Quiz question with options"""
    id: str
    question: str
    options: List[str] = Field(..., min_items=4, max_items=4)
    correct_answer: int = Field(..., ge=0, le=3)
    difficulty: DifficultyLevel
    chapter: str
    explanation: Optional[str] = None


class QuizAttempt(BaseModel):
    """Student's quiz attempt"""
    question_id: str
    selected_answer: int = Field(..., ge=0, le=3)
    time_taken_seconds: int


class QuizSubmission(BaseModel):
    """Quiz submission with all answers"""
    quiz_id: str
    answers: List[QuizAttempt]


class QuizResult(BaseModel):
    """Quiz result summary"""
    quiz_id: str
    score: int
    total_questions: int
    percentage: float
    passed: bool
    time_taken_seconds: int
    chapter_analysis: dict


# ==================== UPLOAD MODELS ====================

class UploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BookUploadResponse(BaseModel):
    """Response after uploading a book"""
    upload_id: str
    filename: str
    status: UploadStatus
    message: str


class UploadProgressResponse(BaseModel):
    """Upload processing progress"""
    upload_id: str
    status: UploadStatus
    progress_percent: int
    chunks_processed: int
    total_chunks: Optional[int]
    error_message: Optional[str] = None


# ==================== ANALYTICS MODELS ====================

class StudentAnalytics(BaseModel):
    """Student performance analytics"""
    student_id: str
    total_quizzes: int
    average_score: float
    total_chats: int
    favorite_subjects: List[str]
    weak_chapters: List[str]
    study_streak_days: int


# ==================== HEALTH CHECK ====================

class HealthCheck(BaseModel):
    """API health check response"""
    status: str
    version: str
    pinecone_status: str
    mongodb_status: str
    redis_status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
