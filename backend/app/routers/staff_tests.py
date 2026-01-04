"""
Staff Tests Router - PDF-based test management
- Teachers upload PDF question papers for specific classes
- Students submit PDF answers
- Teachers comment on submissions
- Teachers upload answer key PDFs
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime
from typing import Optional
import os
import uuid

router = APIRouter(prefix="/api/staff", tags=["staff-tests"])

# In-memory storage (will be replaced with MongoDB)
tests_db = {}
submissions_db = {}
UPLOAD_DIR = "uploads/tests"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/questions", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/answers", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/answer_keys", exist_ok=True)


@router.get("/tests")
async def get_tests(limit: int = 100, class_level: Optional[str] = None):
    """Get all tests (for teachers/admin) or class-specific tests (for students)"""
    tests = list(tests_db.values())
    
    if class_level:
        tests = [t for t in tests if t.get("class_level") == class_level]
    
    # Sort by created_at descending
    tests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return tests[:limit]


@router.post("/tests")
async def create_test(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    class_level: str = Form(...),
    subject: str = Form(...),
    due_date: str = Form(...),
    instructions: str = Form(""),
    created_by: str = Form("admin")
):
    """Create a new PDF-based test"""
    
    # Validate file is PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Generate unique ID
    test_id = str(uuid.uuid4())
    
    # Save the PDF file
    file_path = f"{UPLOAD_DIR}/questions/{test_id}.pdf"
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create test record
    test = {
        "id": test_id,
        "title": title,
        "description": description,
        "class_level": class_level,
        "subject": subject,
        "due_date": due_date,
        "instructions": instructions,
        "created_by": created_by,
        "question_pdf": file_path,
        "answer_key_pdf": None,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "submissions_count": 0
    }
    
    tests_db[test_id] = test
    
    return {"message": "Test created successfully", "test_id": test_id, "test": test}
