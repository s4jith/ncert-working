"""
Notes Service - Handles student notes CRUD operations.
"""

from app.db.mongo import get_notes_collection
from app.models.schemas import Note, NoteCreateRequest
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


class NotesService:
    """Service for managing student notes."""
    
    async def create_note(self, note_request: NoteCreateRequest) -> Note:
        """
        Create a new note in MongoDB.
        
        Args:
            note_request: Note creation request data
        
        Returns:
            Created Note object
        """
        try:
            collection = get_notes_collection()
            
            document = {
                "student_id": note_request.student_id,
                "class_level": note_request.class_level,
                "subject": note_request.subject,
                "chapter": note_request.chapter,
                "page_number": note_request.page_number,
                "highlight_text": note_request.highlight_text,
                "note_content": note_request.note_content,
                "heading": note_request.heading,
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
            
            result = await collection.insert_one(document)
            
            # Return created note
            note = Note(
                id=str(result.inserted_id),
                **document
            )
            
            logger.info(f"✅ Note created: {note.id}")
            return note
        
        except Exception as e:
            logger.error(f"❌ Failed to create note: {e}")
            raise
    
    async def get_notes_by_student(
        self,
        student_id: str,
        class_level: int = None,
        subject: str = None,
        chapter: int = None
    ) -> list[Note]:
        """
        Retrieve notes for a student with optional filters.
        
        Args:
            student_id: Student identifier
            class_level: Optional class filter
            subject: Optional subject filter
            chapter: Optional chapter filter
        
        Returns:
            List of Note objects
        """
        try:
            collection = get_notes_collection()
            
            # Build query
            query = {"student_id": student_id}
            if class_level:
                query["class_level"] = class_level
            if subject:
                query["subject"] = subject
            if chapter:
                query["chapter"] = chapter
            
            # Fetch notes
            cursor = collection.find(query).sort("created_at", -1)
            notes = []
            
            async for doc in cursor:
                note = Note(
                    id=str(doc["_id"]),
                    student_id=doc["student_id"],
                    class_level=doc["class_level"],
                    subject=doc["subject"],
                    chapter=doc["chapter"],
                    page_number=doc["page_number"],
                    highlight_text=doc["highlight_text"],
                    note_content=doc["note_content"],
                    heading=doc.get("heading"),
                    created_at=doc["created_at"],
                    updated_at=doc.get("updated_at")
                )
                notes.append(note)
            
            logger.info(f"✅ Retrieved {len(notes)} notes for student {student_id}")
            return notes
        
        except Exception as e:
            logger.error(f"❌ Failed to retrieve notes: {e}")
            raise
    
    async def update_note(
        self,
        note_id: str,
        note_content: str = None,
        heading: str = None
    ) -> Note:
        """
        Update an existing note.
        
        Args:
            note_id: Note ID
            note_content: Updated content (optional)
            heading: Updated heading (optional)
        
        Returns:
            Updated Note object
        """
        try:
            collection = get_notes_collection()
            
            # Build update document
            update_doc = {"updated_at": datetime.utcnow()}
            if note_content is not None:
                update_doc["note_content"] = note_content
            if heading is not None:
                update_doc["heading"] = heading
            
            # Update note
            result = await collection.find_one_and_update(
                {"_id": ObjectId(note_id)},
                {"$set": update_doc},
                return_document=True
            )
            
            if not result:
                raise ValueError(f"Note {note_id} not found")
            
            # Return updated note
            note = Note(
                id=str(result["_id"]),
                student_id=result["student_id"],
                class_level=result["class_level"],
                subject=result["subject"],
                chapter=result["chapter"],
                page_number=result["page_number"],
                highlight_text=result["highlight_text"],
                note_content=result["note_content"],
                heading=result.get("heading"),
                created_at=result["created_at"],
                updated_at=result.get("updated_at")
            )
            
            logger.info(f"✅ Note updated: {note_id}")
            return note
        
        except Exception as e:
            logger.error(f"❌ Failed to update note: {e}")
            raise
    
    async def delete_note(self, note_id: str) -> bool:
        """
        Delete a note by ID.
        
        Args:
            note_id: Note ID
        
        Returns:
            True if deleted successfully
        """
        try:
            collection = get_notes_collection()
            
            result = await collection.delete_one({"_id": ObjectId(note_id)})
            
            if result.deleted_count == 0:
                raise ValueError(f"Note {note_id} not found")
            
            logger.info(f"✅ Note deleted: {note_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to delete note: {e}")
            raise


# Global notes service instance
notes_service = NotesService()
