"""
Configuration management for NCERT Doubt-Solver FastAPI Backend
Loads settings from environment variables with validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Literal
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "NCERT Doubt-Solver API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-12345"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Database - Pinecone
    VECTOR_DB: Literal["pinecone", "chromadb"] = "pinecone"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "intel_working"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    
    # Database - MongoDB  
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ncert_db"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 864000  # 10 days
    
    # AI Models
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LOCAL_LLM_URL: str = "http://127.0.0.1:1234/v1"
    DEFAULT_LLM: Literal["openai", "gemini", "local"] = "gemini"
    
    # Embedding Model - all-mpnet-base-v2 is best for English semantic search
    # Works well with scientific/technical content (formulas, equations)
    EMBEDDING_MODEL: str = "all-mpnet-base-v2"
    EMBEDDING_DIMENSION: int = 768
    
    # RAG Settings
    RAG_TOP_K: int = 5
    RAG_RERANK_TOP_K: int = 3
    RAG_MIN_RELEVANCE_SCORE: float = 0.7
    
    # Performance
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    # JWT Settings
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg"
    UPLOAD_DIR: str = "media/uploads"
    
    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    class Config:
        env_file = ".env"  # Look in backend folder
        extra = "ignore"  # Ignore extra env vars
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()
