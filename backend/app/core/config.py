"""
Configuration module for NCERT AI Learning Backend.
Loads environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application Info
    APP_NAME: str = "NCERT AI Learning Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MongoDB Atlas
    MONGO_URI: str
    
    # Google Gemini AI
    GEMINI_API_KEY: str
    
    # Pinecone API Key (shared across all indexes)
    PINECONE_API_KEY: str
    
    # Master Index - Subject-wise with Namespaces (NEW ARCHITECTURE)
    PINECONE_MASTER_INDEX: str
    PINECONE_MASTER_HOST: str
    
    # Subject-Wise Pinecone Indexes (Legacy - deprecated)
    # Kept for backward compatibility, but namespaces are used instead
    # Mathematics (Classes 5-12)
    PINECONE_MATH_INDEX: str
    PINECONE_MATH_HOST: str
    
    # Physics (Classes 9-12)
    PINECONE_PHYSICS_INDEX: str
    PINECONE_PHYSICS_HOST: str
    
    # Chemistry (Classes 9-12)
    PINECONE_CHEMISTRY_INDEX: str
    PINECONE_CHEMISTRY_HOST: str
    
    # Biology (Classes 9-12)
    PINECONE_BIOLOGY_INDEX: str
    PINECONE_BIOLOGY_HOST: str
    
    # Social Science (Classes 5-10)
    PINECONE_SOCIAL_INDEX: str
    PINECONE_SOCIAL_HOST: str
    
    # English (Classes 5-12)
    PINECONE_ENGLISH_INDEX: str
    PINECONE_ENGLISH_HOST: str
    
    # Hindi (Classes 5-12)
    PINECONE_HINDI_INDEX: str
    PINECONE_HINDI_HOST: str
    
    # Web Content for DeepDive mode
    PINECONE_WEB_INDEX: str
    PINECONE_WEB_HOST: str
    
    # LLM Generated Content Storage (NEW)
    PINECONE_LLM_INDEX: str = "ncert-llm"
    PINECONE_LLM_HOST: Optional[str] = None
    
    # Legacy index (deprecated - kept for backward compatibility)
    PINECONE_INDEX: str
    PINECONE_HOST: str
    
    # CORS Settings
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Optional fields (for compatibility)
    OPENAI_API_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in .env


# Create global settings instance
settings = Settings()
