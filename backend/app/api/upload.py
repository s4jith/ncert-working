"""
Upload API Routes
PDF/Document upload and processing endpoints
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks

from app.config import settings
from app.api.auth import get_current_active_user, require_role
from app.db.models import BookUploadResponse, UploadProgressResponse, UploadStatus
from app.db.mongodb import get_db
from app.services.document_processor import process_document

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/book", response_model=BookUploadResponse)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    class_num: str = Form(...),
    subject: str = Form(...),
    chapter: Optional[str] = Form(None),
    current_user: dict = Depends(require_role("super_admin"))
):
    """
    Upload NCERT PDF book for processing
    
    The file will be:
    1. Saved to disk
    2. Processed in background (OCR, chunking)
    3. Embedded and stored in Pinecone
    """
    # Validate file type
    if not file.filename.lower().endswith(tuple(settings.allowed_extensions_list)):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Generate unique upload ID
    upload_id = str(uuid.uuid4())
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, upload_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create upload record in MongoDB
    db = get_db()
    upload_record = {
        "_id": upload_id,
        "filename": file.filename,
        "file_path": file_path,
        "class_num": class_num,
        "subject": subject,
        "chapter": chapter,
        "status": UploadStatus.PENDING.value,
        "progress_percent": 0,
        "chunks_processed": 0,
        "total_chunks": None,
        "uploaded_by": str(current_user["_id"]),
        "created_at": datetime.utcnow()
    }
    
    await db.uploaded_books.insert_one(upload_record)
    
    # Start background processing
    background_tasks.add_task(
        process_document,
        upload_id=upload_id,
        file_path=file_path,
        class_num=class_num,
        subject=subject,
        chapter=chapter or f"{subject} Chapter"
    )
    
    return BookUploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        status=UploadStatus.PENDING,
        message="Upload successful. Processing started in background."
    )


@router.get("/status/{upload_id}", response_model=UploadProgressResponse)
async def get_upload_status(
    upload_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get processing status for an upload"""
    db = get_db()
    
    upload = await db.uploaded_books.find_one({"_id": upload_id})
    
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return UploadProgressResponse(
        upload_id=upload_id,
        status=UploadStatus(upload.get("status", "pending")),
        progress_percent=upload.get("progress_percent", 0),
        chunks_processed=upload.get("chunks_processed", 0),
        total_chunks=upload.get("total_chunks"),
        error_message=upload.get("error_message")
    )


@router.post("/image")
async def upload_image_for_ocr(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload an image for OCR text extraction
    Used for image-based question input
    """
    # Validate image file
    valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid image format")
    
    # Save temporarily
    temp_dir = "media/temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(temp_file, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Perform OCR
        from app.services.ocr_service import extract_text_from_image
        extracted_text = await extract_text_from_image(temp_file)
        
        return {
            "success": True,
            "extracted_text": extracted_text,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
