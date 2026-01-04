"""
Main FastAPI Application
NCERT AI Learning Backend

Entry point for the FastAPI application.
Includes all routers, CORS configuration, and database initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.mongo import init_databases, close_databases
from app.routers import chat, mcq, evaluate, notes, assessment, annotation

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for FastAPI application.
    Handles database initialization and cleanup.
    """
    # Startup
    logger.info("🚀 Starting NCERT AI Learning Backend...")
    logger.info(f"   App: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   Debug Mode: {settings.DEBUG}")
    
    try:
        await init_databases()
        logger.info("✅ All systems initialized successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down NCERT AI Learning Backend...")
    await close_databases()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## NCERT AI Learning Backend
    
    A production-grade educational AI system for NCERT students (Classes 5-10).
    
    ### Features:
    - **RAG-based Chatbot**: Context-aware explanations using Pinecone + Gemini
    - **AI MCQ Generation**: Concept-based questions using chapter content
    - **Automated Evaluation**: Score calculation and personalized feedback
    - **Student Notes**: CRUD operations with MongoDB Atlas
    - **Multi-mode Learning**: Simple, Meaning, Story, Example, Summary modes
    
    ### Tech Stack:
    - **Backend**: FastAPI + Python 3
    - **AI**: Google Gemini 1.5 Flash + text-embedding-004
    - **Vector DB**: Pinecone
    - **Database**: MongoDB Atlas
    
    ### Architecture:
    All endpoints follow strict RAG principles - no hallucination, only context-based answers.
    """,
    lifespan=lifespan,
    debug=settings.DEBUG
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Alternative React dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(mcq.router, prefix="/api")
app.include_router(evaluate.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")  # ✅ Voice Assessment
app.include_router(annotation.router, prefix="/api")  # ✅ Annotation Chatbot

# Import admin and user routers
from app.routers import admin, user, test, auth
from app.routers import admin_dashboard, support, support_tickets, test_management
from app.routers import book_management
from app.routers import admin_intel  # Intel OPEA-style admin endpoint
app.include_router(admin.router, prefix="/api")  # ✅ Admin & Monitoring
app.include_router(admin_intel.router)           # ✅ Intel Status Endpoint
app.include_router(user.router, prefix="/api")   # ✅ User Stats (Dashboard)
app.include_router(test.router, prefix="/api")   # ✅ Tests (Staff + AI)
app.include_router(auth.router)                  # ✅ Authentication (Login/Password)
app.include_router(admin_dashboard.router)       # ✅ Admin Dashboard & Student Management
app.include_router(support.router)               # ✅ Support (FAQs, Contact, Feedback)
app.include_router(support_tickets.router)       # ✅ Support Tickets
app.include_router(test_management.router)       # ✅ Test Management (PDF Tests, Submissions, Feedback)
app.include_router(book_management.router)       # ✅ Book Management (Admin upload, Student view)

# Stretch goal routers (Intel Unnati)
from app.routers import voice_chat, student_level, multilingual_chat, optimized_chat
app.include_router(voice_chat.router)            # ✅ Voice Chat (Stretch Goal)
app.include_router(student_level.router)         # ✅ Adaptive Explanations (Stretch Goal)
app.include_router(multilingual_chat.router)     # ✅ Multilingual Chat (Indian Languages)
app.include_router(optimized_chat.router, prefix="/api")  # ⚡ Optimized Chat (2-call max)


# Root endpoint
@app.get("/", tags=["Health Check"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "NCERT AI Learning Backend",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health", tags=["Health Check"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
