"""
NCERT Doubt-Solver FastAPI Main Application
OPEA-based RAG Pipeline for Multilingual Q&A
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.api import auth, chat, quiz, admin, upload
from app.db.pinecone import init_pinecone, close_pinecone
from app.db.mongodb import init_mongodb, close_mongodb
from app.db.models import HealthCheck

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting NCERT Doubt-Solver API...")
    
    # Initialize databases (gracefully handle failures)
    try:
        await init_mongodb()
        logger.info("✅ MongoDB connected")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB unavailable: {e}")
    
    try:
        init_pinecone()
        logger.info("✅ Pinecone connected")
    except Exception as e:
        logger.warning(f"⚠️ Pinecone unavailable: {e}")
    
    logger.info(f"✅ Server ready on port 8000")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await close_mongodb()
    close_pinecone()
    logger.info("👋 Goodbye!")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Multilingual NCERT Doubt-Solver API
    
    A RAG-based Q&A system for NCERT textbooks (Grades 5-12) with:
    - 🎯 Grade-specific retrieval and filtering
    - 🌍 Multilingual support (English, Hindi, Urdu, regional languages)
    - 💬 Conversational AI with citations
    - 🎤 Voice I/O capabilities
    - 📊 Quiz and assessment system
    
    Built with OPEA architecture for optimal performance.
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Register API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat & RAG"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz System"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(upload.router, prefix="/api/upload", tags=["File Upload"])


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Check API and all service connections"""
    from app.db.pinecone import check_pinecone_health
    from app.db.mongodb import check_mongodb_health
    
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION,
        pinecone_status=await check_pinecone_health(),
        mongodb_status=await check_mongodb_health(),
        redis_status="connected",  # TODO: Implement Redis check
    )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root - basic info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health"
    }


# Mount static files for uploaded content (if exists)
import os
media_dir = "media"
if not os.path.exists(media_dir):
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(os.path.join(media_dir, "uploads"), exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=4 if not settings.DEBUG else 1
    )
