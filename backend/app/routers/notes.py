"""
Notes Router - Student notes CRUD endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import NoteCreateRequest, Note, NotesListResponse, SuccessResponse
from app.services.notes_service import notes_service
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notes",
    tags=["Notes"]
)


@router.post("/", response_model=Note)
async def create_note(request: NoteCreateRequest):
    """
    Create a new student note.
    
    Saves note to MongoDB Atlas with metadata including:
    - Student ID
    - Class, subject, chapter
    - Page number
    - Highlighted text
    - Note content and optional heading
    """
    try:
        logger.info(f"Create note request: Student {request.student_id}, Class {request.class_level}, {request.subject}, Ch. {request.chapter}")
        
        note = await notes_service.create_note(request)
        return note
    
    except Exception as e:
        logger.error(f"❌ Create note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}", response_model=NotesListResponse)
async def get_notes(
    student_id: str,
    class_level: Optional[int] = Query(None, ge=5, le=10),
    subject: Optional[str] = Query(None),
    chapter: Optional[int] = Query(None, ge=1)
):
    """
    Retrieve notes for a student with optional filters.
    
    **Query Parameters:**
    - `class_level`: Filter by class (5-10)
    - `subject`: Filter by subject
    - `chapter`: Filter by chapter number
    """
    try:
        logger.info(f"Get notes request: Student {student_id}")
        
        notes = await notes_service.get_notes_by_student(
            student_id=student_id,
            class_level=class_level,
            subject=subject,
            chapter=chapter
        )
        
        return NotesListResponse(
            notes=notes,
            total=len(notes)
        )
    
    except Exception as e:
        logger.error(f"❌ Get notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{note_id}", response_model=Note)
async def update_note(
    note_id: str,
    note_content: Optional[str] = None,
    heading: Optional[str] = None
):
    """
    Update an existing note.
    
    **Parameters:**
    - `note_id`: MongoDB document ID
    - `note_content`: Updated note content (optional)
    - `heading`: Updated heading (optional)
    """
    try:
        logger.info(f"Update note request: {note_id}")
        
        note = await notes_service.update_note(
            note_id=note_id,
            note_content=note_content,
            heading=heading
        )
        
        return note
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Update note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{note_id}", response_model=SuccessResponse)
async def delete_note(note_id: str):
    """
    Delete a note by ID.
    
    **Parameters:**
    - `note_id`: MongoDB document ID
    """
    try:
        logger.info(f"Delete note request: {note_id}")
        
        await notes_service.delete_note(note_id)
        
        return SuccessResponse(
            message=f"Note {note_id} deleted successfully"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Delete note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
