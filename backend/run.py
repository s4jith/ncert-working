"""
Run script for NCERT AI Learning Backend.
Start the FastAPI server with uvicorn.
"""

import uvicorn
from app.core.config import settings
from app.main import app  # Expose FastAPI app for `uvicorn run:app`

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 Starting {settings.APP_NAME}")
    print(f"   Version: {settings.APP_VERSION}")
    print(f"   Host: {settings.HOST}:{settings.PORT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 60)
    
    # You can also run: `uvicorn run:app --reload --port 8000`
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
