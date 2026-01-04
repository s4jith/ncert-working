"""
Book Management Router

Admin endpoints for managing books:
- Upload new books (PDF + metadata → MongoDB + Pinecone)
- List all books
- Delete books (from both MongoDB and Pinecone)
- Get books by class/subject for student view

Student endpoints:
- Get available subjects for their class
- Get chapters/lessons for a subject
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import os
import uuid
import shutil
import logging
import asyncio
from bson import ObjectId

from app.db.mongo import db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/books", tags=["Book Management"])

# Directory for storing uploaded PDFs
# __file__ is in routers/, go up 1 level to app/, then into uploads/books
BOOKS_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "books")
os.makedirs(BOOKS_UPLOAD_DIR, exist_ok=True)


# ==================== HELPER FUNCTIONS ====================

async def process_book_embeddings(
    book_id: str,
    pdf_path: str,
    book_metadata: Dict,
    namespace: str
) -> Dict:
    """
    Process a PDF and generate embeddings for Pinecone.
    
    This function:
    1. Extracts text from PDF using PyPDF2 and OCR
    2. Handles images, formulas, and diagrams
    3. Chunks the content appropriately
    4. Generates embeddings using Gemini
    5. Uploads to Pinecone
    
    Returns statistics about the processing.
    """
    try:
        from app.services.pdf_processor import AdvancedPDFProcessor, PineconeEmbeddingUploader
        
        logger.info(f"🔄 Starting embedding generation for book: {book_id}")
        
        # Initialize processors
        pdf_processor = AdvancedPDFProcessor(
            chunk_size=800,
            chunk_overlap=150,
            dpi=200,  # Balance between quality and speed
            use_gemini_vision=True
        )
        
        uploader = PineconeEmbeddingUploader()
        
        # Process PDF
        logger.info("📄 Processing PDF...")
        result = pdf_processor.process_pdf(
            pdf_path=pdf_path,
            book_metadata=book_metadata
        )
        
        if not result.success:
            return {
                "success": False,
                "error": "PDF processing failed",
                "errors": result.errors,
                "total_pages": result.total_pages,
                "processed_pages": result.processed_pages
            }
        
        # Create chunks
        logger.info("📦 Creating chunks...")
        chunks = pdf_processor.create_chunks(result.pages, book_metadata)
        
        if not chunks:
            return {
                "success": False,
                "error": "No content extracted from PDF",
                "total_pages": result.total_pages,
                "total_chunks": 0
            }
        
        # Upload to Pinecone
        logger.info(f"🚀 Uploading {len(chunks)} chunks to Pinecone...")
        upload_stats = uploader.upload_chunks(chunks, namespace)
        
        return {
            "success": upload_stats['successful'] > 0,
            "total_pages": result.total_pages,
            "processed_pages": result.processed_pages,
            "total_chunks": len(chunks),
            "embedding_count": upload_stats['successful'],
            "failed_embeddings": upload_stats['failed'],
            "errors": result.errors + upload_stats.get('errors', []),
            "processing_time": result.processing_time,
            "namespace": namespace
        }
        
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "errors": [str(e)]
        }


# ==================== MODELS ====================

class BookCreate(BaseModel):
    title: str
    subject: str
    class_level: int
    description: Optional[str] = ""
    
class ChapterCreate(BaseModel):
    book_id: str
    chapter_number: int
    title: str
    description: Optional[str] = ""

class BookResponse(BaseModel):
    id: str
    title: str
    subject: str
    class_level: int
    description: str
    pdf_filename: str
    pdf_url: str
    has_embeddings: bool
    embedding_count: int
    chapters: List[dict]
    created_at: str
    updated_at: str


# ==================== ADMIN ENDPOINTS ====================

@router.post("/upload")
async def upload_book(
    title: str = Form(...),
    subject: str = Form(...),
    class_level: int = Form(...),
    chapter_number: int = Form(1),
    description: str = Form(""),
    generate_embeddings: bool = Form(True),
    pdf_file: UploadFile = File(...)
):
    """
    Upload a new book chapter PDF, store metadata in MongoDB, and generate embeddings.
    
    This endpoint:
    1. Saves the PDF file
    2. Stores book metadata in MongoDB
    3. Processes the PDF (OCR, text extraction, image analysis)
    4. Generates embeddings for all content
    5. Uploads embeddings to Pinecone
    
    Namespace Organization:
    - All chapters of a subject are stored in one namespace
    - Mathematics: all class 6-12 math chapters
    - Physics: all class 6-12 physics chapters
    - Chemistry: all class 6-12 chemistry chapters
    - Metadata includes class_level and chapter_number for filtering
    
    Args:
        title: Book/Chapter title
        subject: Subject (Mathematics, Physics, Chemistry, etc.)
        class_level: Class level (6-12)
        chapter_number: Chapter number (1-50)
        description: Optional description
        generate_embeddings: Whether to generate and upload embeddings (default: True)
        pdf_file: The PDF file to upload
    """
    try:
        # Validate PDF file
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create organized folder structure: class_XX/subject/chapter_XX/
        class_folder = f"class_{class_level}"
        subject_folder = subject.lower().replace(' ', '_')
        chapter_folder = f"chapter_{chapter_number}"
        
        # Build the directory path
        book_dir = os.path.join(BOOKS_UPLOAD_DIR, class_folder, subject_folder, chapter_folder)
        logger.info(f"📁 Creating directory: {book_dir}")
        os.makedirs(book_dir, exist_ok=True)
        
        # Generate clean filename
        clean_title = title.replace(' ', '_').replace('/', '_')[:50]  # Limit length
        safe_filename = f"{clean_title}.pdf"
        file_path = os.path.join(book_dir, safe_filename)
        
        # Save the file with verification
        logger.info(f"📄 Saving PDF to: {file_path}")
        content = await pdf_file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to save PDF file to disk")
        
        file_size = os.path.getsize(file_path)
        logger.info(f"✅ PDF saved successfully: {file_path} ({file_size} bytes)")
        
        # Reset file position for embedding processing
        await pdf_file.seek(0)
        
        # Create relative path for storing in DB
        relative_path = f"{class_folder}/{subject_folder}/{chapter_folder}/{safe_filename}"
        
        logger.info(f"📁 Saved PDF: {relative_path}")
        
        # Create namespace for embeddings - ONE namespace per subject (all classes together)
        # This allows the bot to retrieve from all class levels for comprehensive answers
        namespace = subject.lower().replace(' ', '_')
        
        # Generate a unique book_id (for compatibility with old system)
        book_id = str(uuid.uuid4())
        
        # Create book document
        book_doc = {
            "book_id": book_id,  # Add book_id for unique index
            "title": title,
            "subject": subject,
            "class_level": class_level,
            "chapter_number": chapter_number,
            "description": description,
            "pdf_filename": safe_filename,
            "pdf_path": relative_path,  # Store organized path
            "pdf_url": f"/api/books/pdf/{relative_path}",  # URL with full path
            "has_embeddings": False,
            "embedding_count": 0,
            "embedding_namespace": namespace,
            "chapters": [],
            "processing_status": "pending" if generate_embeddings else "uploaded",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        result = db.books.insert_one(book_doc)
        mongo_id = str(result.inserted_id)
        
        logger.info(f"✅ Book record created: {title} (ID: {mongo_id}, book_id: {book_id})")
        
        # Generate embeddings if requested
        embedding_result = None
        if generate_embeddings:
            try:
                # Update status to processing
                db.books.update_one(
                    {"_id": ObjectId(mongo_id)},
                    {"$set": {"processing_status": "processing"}}
                )
                
                # Process PDF and generate embeddings
                embedding_result = await process_book_embeddings(
                    book_id=book_id,  # Use book_id for embeddings metadata
                    pdf_path=file_path,
                    book_metadata={
                        "book_id": book_id,
                        "title": title,
                        "subject": subject,
                        "class_level": class_level,
                        "chapter_number": chapter_number
                    },
                    namespace=namespace
                )
                
                # Update book with embedding info
                db.books.update_one(
                    {"_id": ObjectId(mongo_id)},
                    {
                        "$set": {
                            "has_embeddings": embedding_result.get("success", False),
                            "embedding_count": embedding_result.get("embedding_count", 0),
                            "total_pages": embedding_result.get("total_pages", 0),
                            "total_chunks": embedding_result.get("total_chunks", 0),
                            "processing_status": "completed" if embedding_result.get("success") else "failed",
                            "processing_errors": embedding_result.get("errors", []),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"✅ Embeddings generated: {embedding_result.get('embedding_count', 0)} vectors")
                
            except Exception as e:
                logger.error(f"❌ Embedding generation failed: {e}")
                db.books.update_one(
                    {"_id": ObjectId(mongo_id)},
                    {
                        "$set": {
                            "processing_status": "failed",
                            "processing_errors": [str(e)],
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                embedding_result = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "message": f"Book '{title}' uploaded successfully",
            "book_id": mongo_id,  # Return MongoDB _id for frontend
            "pdf_url": book_doc["pdf_url"],
            "embeddings": embedding_result
        }
        
    except Exception as e:
        logger.error(f"❌ Book upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{book_id}/regenerate-embeddings")
async def regenerate_embeddings(book_id: str):
    """
    Regenerate embeddings for an existing book.
    Useful if initial embedding generation failed or you want to update embeddings.
    """
    try:
        # Get book from database
        book = db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Get PDF path
        pdf_path = os.path.join(BOOKS_UPLOAD_DIR, book["pdf_filename"])
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        # Update status
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {"$set": {"processing_status": "processing", "updated_at": datetime.utcnow()}}
        )
        
        # Process embeddings
        namespace = book.get("embedding_namespace", f"{book['subject'].lower().replace(' ', '_')}_class{book['class_level']}")
        
        result = await process_book_embeddings(
            book_id=book_id,
            pdf_path=pdf_path,
            book_metadata={
                "book_id": book_id,
                "title": book["title"],
                "subject": book["subject"],
                "class_level": book["class_level"]
            },
            namespace=namespace
        )
        
        # Update book with results
        db.books.update_one(
            {"_id": ObjectId(book_id)},
            {
                "$set": {
                    "has_embeddings": result.get("success", False),
                    "embedding_count": result.get("embedding_count", 0),
                    "total_pages": result.get("total_pages", 0),
                    "total_chunks": result.get("total_chunks", 0),
                    "processing_status": "completed" if result.get("success") else "failed",
                    "processing_errors": result.get("errors", []),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": result.get("success", False),
            "message": f"Embeddings {'regenerated' if result.get('success') else 'failed to regenerate'}",
            "details": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Regenerate embeddings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{book_id}/chapters")
async def add_chapter(book_id: str, chapter: ChapterCreate):
    """Add a chapter to a book."""
    try:
        chapter_doc = {
            "chapter_number": chapter.chapter_number,
            "title": chapter.title,
            "description": chapter.description,
            "page_start": 1,
            "page_end": None
        }
        
        result = db.books.update_one(
            {"_id": ObjectId(book_id)},
            {
                "$push": {"chapters": chapter_doc},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return {"success": True, "message": "Chapter added successfully"}
        
    except Exception as e:
        logger.error(f"❌ Add chapter failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/list")
async def list_all_books():
    """List all books for admin view."""
    try:
        books = list(db.books.find().sort("created_at", -1))
        
        result = []
        for book in books:
            result.append({
                "id": str(book["_id"]),
                "title": book.get("title", "Untitled"),
                "subject": book.get("subject", "Unknown"),
                "class_level": book.get("class_level", 6),  # Default to 6 if missing
                "description": book.get("description", ""),
                "pdf_filename": book.get("pdf_filename", ""),
                "pdf_url": book.get("pdf_url", ""),
                "has_embeddings": book.get("has_embeddings", False),
                "embedding_count": book.get("embedding_count", 0),
                "chapters": book.get("chapters", []),
                "created_at": book["created_at"].isoformat() if book.get("created_at") else "",
                "updated_at": book["updated_at"].isoformat() if book.get("updated_at") else ""
            })
        
        return {"books": result, "total": len(result)}
        
    except Exception as e:
        logger.error(f"❌ List books failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{book_id}")
async def delete_book(book_id: str, delete_embeddings: bool = Query(default=True)):
    """
    Delete a book from MongoDB and optionally from Pinecone.
    """
    try:
        # Get book info first
        book = db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Delete PDF file
        pdf_path = os.path.join(BOOKS_UPLOAD_DIR, book["pdf_filename"])
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"Deleted PDF file: {pdf_path}")
        
        # Delete embeddings from Pinecone if requested
        if delete_embeddings and book.get("has_embeddings"):
            try:
                from pinecone import Pinecone
                pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                index = pc.Index(host=settings.PINECONE_HOST)
                
                # Delete by metadata filter (book_id)
                namespace = book.get("embedding_namespace", "default")
                
                # Delete all vectors with this book_id
                # Note: Pinecone delete by filter requires specific setup
                # For now, we'll log the namespace for manual cleanup
                logger.info(f"Embeddings in namespace '{namespace}' should be deleted for book_id: {book_id}")
                
                # If using metadata filter delete (Pinecone serverless supports this):
                try:
                    index.delete(
                        filter={"book_id": book_id},
                        namespace=namespace
                    )
                    logger.info(f"✅ Deleted embeddings for book {book_id} from Pinecone")
                except Exception as pe:
                    logger.warning(f"Could not delete embeddings: {pe}")
                
            except Exception as e:
                logger.warning(f"Pinecone cleanup failed: {e}")
        
        # Delete from MongoDB
        db.books.delete_one({"_id": ObjectId(book_id)})
        
        logger.info(f"✅ Book deleted: {book['title']} (ID: {book_id})")
        
        return {
            "success": True,
            "message": f"Book '{book['title']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete book failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{book_id}/generate-embeddings")
async def generate_embeddings(book_id: str):
    """
    Trigger embedding generation for a book.
    This is a placeholder - actual embedding generation should be done via script.
    """
    try:
        book = db.books.find_one({"_id": ObjectId(book_id)})
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # For now, just return instructions
        return {
            "success": True,
            "message": "Embedding generation triggered",
            "instructions": f"""
To generate embeddings, run the following script:
python backend/scripts/upload_pdfs_to_pinecone.py --book-id {book_id}

Or use the existing multimodal uploader for math/physics content.
            """,
            "book_id": book_id,
            "pdf_path": os.path.join(BOOKS_UPLOAD_DIR, book["pdf_filename"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Generate embeddings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{book_id}/embeddings-status")
async def update_embedding_status(
    book_id: str,
    has_embeddings: bool = Query(...),
    embedding_count: int = Query(default=0)
):
    """Update the embedding status of a book (called after embedding generation)."""
    try:
        result = db.books.update_one(
            {"_id": ObjectId(book_id)},
            {
                "$set": {
                    "has_embeddings": has_embeddings,
                    "embedding_count": embedding_count,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return {"success": True, "message": "Embedding status updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update embedding status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STUDENT ENDPOINTS ====================

@router.get("/student/subjects")
async def get_available_subjects(class_level: int = Query(...)):
    """
    Get list of subjects that have books available for a class level.
    Queries Pinecone to get real data about which subjects have content for this class.
    """
    try:
        from pinecone import Pinecone
        import random
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        # Get index stats to see all namespaces (subjects)
        stats = index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        
        subject_info = []
        
        # Use a random vector for querying (zero vector doesn't work well)
        random_vec = [random.random() for _ in range(768)]
        
        for namespace, ns_data in namespaces.items():
            if ns_data.get("vector_count", 0) == 0:
                continue
                
            # Query this namespace to check if it has vectors for this class level
            try:
                # First, query without filter to see what class levels exist
                sample_response = index.query(
                    namespace=namespace,
                    vector=random_vec,
                    top_k=50,
                    include_metadata=True
                )
                
                matches = sample_response.get("matches", [])
                
                # Check if any match has the target class level
                has_class = False
                for match in matches:
                    metadata = match.get("metadata", {})
                    # Check various class level field names
                    meta_class = metadata.get("class_level") or metadata.get("class")
                    if meta_class is not None:
                        # Handle string or int
                        if isinstance(meta_class, str):
                            try:
                                if "class" in meta_class.lower():
                                    meta_class = int(meta_class.lower().replace("class", "").strip())
                                else:
                                    meta_class = int(meta_class)
                            except:
                                continue
                        if int(meta_class) == class_level:
                            has_class = True
                            break
                
                if has_class or (matches and len(matches) > 0 and matches[0].get("metadata", {}).get("class_level") is None):
                    # This subject has content for this class OR has no class metadata (old data)
                    # Format subject name nicely
                    subject_name = namespace.replace('_', ' ').title()
                    
                    # Count vectors for this class in this namespace
                    vector_count = ns_data.get("vector_count", 0)
                    
                    subject_info.append({
                        "name": subject_name,
                        "namespace": namespace,
                        "vector_count": vector_count,
                        "has_ai_support": True
                    })
                    
            except Exception as e:
                logger.warning(f"Error querying namespace {namespace}: {e}")
                continue
        
        # Sort by name
        subject_info.sort(key=lambda x: x["name"])
        
        logger.info(f"📚 Found {len(subject_info)} subjects with content for Class {class_level}")
        
        return {"subjects": subject_info, "class_level": class_level}
        
    except Exception as e:
        logger.error(f"❌ Get subjects failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/books")
async def get_books_for_student(
    class_level: int = Query(...),
    subject: str = Query(...)
):
    """Get books/lessons for a student based on class and subject."""
    try:
        books = list(db.books.find({
            "class_level": class_level,
            "subject": subject
        }).sort("created_at", 1))
        
        result = []
        for book in books:
            # Create lesson-like structure for compatibility with BookToBot
            result.append({
                "id": str(book["_id"]),
                "title": book["title"],
                "description": book.get("description", ""),
                "subject": book["subject"],
                "classLevel": book["class_level"],
                "pdfUrl": book["pdf_url"],
                "has_ai_support": book.get("has_embeddings", False),
                "chapters": book.get("chapters", [])
            })
        
        return {"books": result, "total": len(result)}
        
    except Exception as e:
        logger.error(f"❌ Get student books failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/lessons")
async def get_lessons_for_student(
    class_level: int = Query(...),
    subject: str = Query(...)
):
    """
    Get lessons/chapters for a student from Pinecone metadata.
    Returns in a format compatible with the existing BookToBot component.
    """
    try:
        from pinecone import Pinecone
        import random
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        # Normalize subject to namespace format
        namespace = subject.lower().replace(' ', '_')
        
        # Use random vector for querying (zero vector doesn't work well with cosine similarity)
        random_vec = [random.random() for _ in range(768)]
        
        # Query Pinecone for vectors - get a good sample
        query_response = index.query(
            namespace=namespace,
            vector=random_vec,
            top_k=10000,
            include_metadata=True
        )
        
        matches = query_response.get("matches", [])
        
        # Filter and group by chapter for this class level
        chapters_found = {}
        for match in matches:
            metadata = match.get("metadata", {})
            
            # Check class level
            meta_class = metadata.get("class_level") or metadata.get("class")
            if meta_class is not None:
                # Handle string class levels
                if isinstance(meta_class, str):
                    try:
                        if "class" in meta_class.lower():
                            meta_class = int(meta_class.lower().replace("class", "").strip())
                        else:
                            meta_class = int(meta_class)
                    except:
                        continue
                if int(meta_class) != class_level:
                    continue  # Skip if not matching class
            
            # Extract chapter number (handle different field names)
            chapter_num = metadata.get("chapter_number") or metadata.get("chapter") or 1
            # Handle string chapter numbers
            if isinstance(chapter_num, str):
                try:
                    if "chapter" in chapter_num.lower():
                        chapter_num = int(chapter_num.lower().replace("chapter", "").strip())
                    else:
                        chapter_num = int(chapter_num)
                except:
                    chapter_num = 1
            
            chapter_num = int(chapter_num)
            
            if chapter_num not in chapters_found:
                # Get title from metadata
                title = metadata.get("book_title") or metadata.get("title") or metadata.get("chapter_title") or f"Chapter {chapter_num}"
                
                chapters_found[chapter_num] = {
                    "chapter_number": chapter_num,
                    "title": title,
                    "vector_count": 0,
                    "pdf_url": metadata.get("pdf_url", "")
                }
            
            chapters_found[chapter_num]["vector_count"] += 1
        
        # Also check MongoDB for PDF URLs
        mongo_books = list(db.books.find({
            "class_level": class_level,
            "subject": {"$regex": f"^{subject}$", "$options": "i"}
        }).sort("chapter_number", 1))
        
        # Build lessons list
        lessons = []
        lesson_number = 1
        
        for chapter_num in sorted(chapters_found.keys()):
            chapter_data = chapters_found[chapter_num]
            
            # Try to get PDF URL from MongoDB
            pdf_url = chapter_data.get("pdf_url", "")
            book_record = None
            
            for book in mongo_books:
                if book.get("chapter_number") == chapter_num:
                    book_record = book
                    pdf_url = book.get("pdf_url", "")
                    break
            
            lessons.append({
                "id": f"{namespace}_{class_level}_{chapter_num}",
                "number": lesson_number,
                "title": chapter_data["title"],
                "description": f"{chapter_data['vector_count']} AI-indexed content blocks",
                "pdfUrl": pdf_url,
                "subject": subject,
                "classLevel": class_level,
                "has_ai_support": True,
                "chapter_number": chapter_num,
                "book_id": str(book_record["_id"]) if book_record else None
            })
            lesson_number += 1
        
        logger.info(f"📚 Found {len(lessons)} chapters for {subject} Class {class_level}")
        
        return {
            "lessons": lessons,
            "total": len(lessons),
            "subject": subject,
            "class_level": class_level
        }
        
    except Exception as e:
        logger.error(f"❌ Get lessons failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PDF SERVING ====================

@router.get("/pdf/{file_path:path}")
async def serve_pdf(file_path: str):
    """
    Serve a book PDF file from organized folder structure.
    Path format: class_XX/subject/chapter_XX/filename.pdf
    """
    try:
        # Build full file path
        full_path = os.path.join(BOOKS_UPLOAD_DIR, file_path)
        
        # Security check: ensure path is within BOOKS_UPLOAD_DIR
        real_books_dir = os.path.realpath(BOOKS_UPLOAD_DIR)
        real_file_path = os.path.realpath(full_path)
        
        if not real_file_path.startswith(real_books_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(full_path):
            logger.error(f"PDF not found: {full_path}")
            raise HTTPException(status_code=404, detail=f"PDF not found: {file_path}")
        
        # Get filename for download
        filename = os.path.basename(file_path)
        
        logger.info(f"📄 Serving PDF: {file_path}")
        
        return FileResponse(
            full_path,
            media_type="application/pdf",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Serve PDF failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SYNC EXISTING DATA ====================

@router.post("/admin/sync-existing")
async def sync_existing_books():
    """
    Sync existing books from frontend lessons.js to MongoDB.
    This preserves the current math books that are already in Pinecone.
    """
    try:
        # Check if already synced
        existing_count = db.books.count_documents({})
        if existing_count > 0:
            return {
                "success": True,
                "message": f"Already have {existing_count} books in database",
                "synced": 0
            }
        
        # Define the existing math lessons (from lessons.js)
        math_lessons = [
            {"number": 1, "title": "Patterns in Mathematics", "description": "Exploring patterns in numbers, shapes, and their relationships.", "pdfUrl": "/fegp101.pdf"},
            {"number": 2, "title": "Lines and Angles", "description": "Understanding different types of lines, angles, and their properties.", "pdfUrl": "/fegp102.pdf"},
            {"number": 3, "title": "Number Play", "description": "Playing with numbers, divisibility rules, and number patterns.", "pdfUrl": "/fegp103.pdf"},
            {"number": 4, "title": "Data Handling and Presentation", "description": "Collecting, organizing, and representing data using graphs and charts.", "pdfUrl": "/fegp104.pdf"},
            {"number": 5, "title": "Prime Time", "description": "Understanding prime numbers, factors, and multiples.", "pdfUrl": "/fegp105.pdf"},
            {"number": 6, "title": "Perimeter and Area", "description": "Calculating perimeter and area of various shapes.", "pdfUrl": "/fegp106.pdf"},
            {"number": 7, "title": "Fractions", "description": "Understanding fractions, equivalent fractions, and operations.", "pdfUrl": "/fegp107.pdf"},
            {"number": 8, "title": "Playing with Constructions", "description": "Geometric constructions using compass and ruler.", "pdfUrl": "/fegp108.pdf"},
            {"number": 9, "title": "Symmetry", "description": "Exploring symmetry in shapes and patterns.", "pdfUrl": "/fegp109.pdf"},
            {"number": 10, "title": "The Other Side of Zero", "description": "Introduction to negative numbers and integers.", "pdfUrl": "/fegp110.pdf"},
        ]
        
        # Create a single book entry for Math Class 6
        math_book = {
            "title": "Mathematics - Class 6",
            "subject": "Mathematics",
            "class_level": 6,
            "description": "NCERT Mathematics textbook for Class 6",
            "pdf_filename": "fegp101.pdf",  # First chapter
            "pdf_url": "/fegp101.pdf",  # Points to public folder
            "has_embeddings": True,  # Already in Pinecone
            "embedding_count": 2193,  # From README
            "embedding_namespace": "mathematics",
            "chapters": [
                {
                    "chapter_number": lesson["number"],
                    "title": lesson["title"],
                    "description": lesson["description"],
                    "pdf_url": lesson["pdfUrl"]
                }
                for lesson in math_lessons
            ],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db.books.insert_one(math_book)
        
        # Also add individual entries for each chapter (for backward compatibility)
        for lesson in math_lessons:
            chapter_book = {
                "title": lesson["title"],
                "subject": "Mathematics",
                "class_level": 6,
                "description": lesson["description"],
                "pdf_filename": lesson["pdfUrl"].replace("/", ""),
                "pdf_url": lesson["pdfUrl"],
                "has_embeddings": True,
                "embedding_count": 0,  # Individual count unknown
                "embedding_namespace": "mathematics",
                "chapter_number": lesson["number"],
                "is_chapter": True,
                "chapters": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            db.books.insert_one(chapter_book)
        
        logger.info("✅ Synced existing Math lessons to MongoDB")
        
        return {
            "success": True,
            "message": "Synced existing books to MongoDB",
            "synced": len(math_lessons) + 1
        }
        
    except Exception as e:
        logger.error(f"❌ Sync existing books failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PINECONE STATS ====================

@router.get("/admin/pinecone-stats")
async def get_pinecone_stats():
    """Get Pinecone index statistics."""
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(host=settings.PINECONE_HOST)
        
        stats = index.describe_index_stats()
        
        # Convert namespaces to serializable format
        namespaces_dict = {}
        raw_namespaces = stats.get("namespaces", {})
        
        if isinstance(raw_namespaces, dict):
            for ns_name, ns_data in raw_namespaces.items():
                if hasattr(ns_data, 'vector_count'):
                    # Pinecone SDK object
                    namespaces_dict[ns_name] = {
                        "vector_count": ns_data.vector_count
                    }
                elif isinstance(ns_data, dict):
                    # Already a dict
                    namespaces_dict[ns_name] = {
                        "vector_count": ns_data.get("vector_count", 0)
                    }
                else:
                    # Try to convert to dict
                    try:
                        namespaces_dict[ns_name] = {"vector_count": int(ns_data)}
                    except:
                        namespaces_dict[ns_name] = {"vector_count": 0}
        
        return {
            "success": True,
            "stats": {
                "total_vector_count": int(stats.get("total_vector_count", 0)),
                "dimension": int(stats.get("dimension", 0)),
                "namespaces": namespaces_dict
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Get Pinecone stats failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "stats": {
                "total_vector_count": 0,
                "dimension": 0,
                "namespaces": {}
            }
        }


@router.post("/admin/fix-missing-fields")
async def fix_missing_fields():
    """
    Fix any books in the database that are missing required fields.
    This is a migration endpoint to handle legacy data.
    """
    try:
        # Find all books
        all_books = list(db.books.find())
        fixed_count = 0
        
        for book in all_books:
            needs_update = False
            update_data = {}
            
            # Check for missing class_level
            if "class_level" not in book:
                update_data["class_level"] = 6  # Default to class 6
                needs_update = True
            
            # Check for missing title
            if "title" not in book or not book.get("title"):
                update_data["title"] = f"Untitled Book ({book['_id']})"
                needs_update = True
            
            # Check for missing subject
            if "subject" not in book or not book.get("subject"):
                update_data["subject"] = "Unknown"
                needs_update = True
            
            # Check for missing pdf_filename
            if "pdf_filename" not in book or not book.get("pdf_filename"):
                update_data["pdf_filename"] = ""
                needs_update = True
            
            # Check for missing pdf_url
            if "pdf_url" not in book or not book.get("pdf_url"):
                update_data["pdf_url"] = ""
                needs_update = True
            
            # Update if needed
            if needs_update:
                db.books.update_one(
                    {"_id": book["_id"]},
                    {"$set": update_data}
                )
                fixed_count += 1
                logger.info(f"Fixed book {book['_id']}: {update_data}")
        
        return {
            "success": True,
            "message": f"Fixed {fixed_count} books with missing fields",
            "total_books": len(all_books),
            "fixed_count": fixed_count
        }
        
    except Exception as e:
        logger.error(f"❌ Fix missing fields failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/hierarchical-structure")
async def get_hierarchical_structure():
    """
    Get the hierarchical structure of books from Pinecone metadata.
    Returns: { subjects: { [subject]: { classes: { [class]: { chapters: [chapter_numbers] } } } } }
    
    This queries actual Pinecone data to show what's really stored.
    """
    try:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        # Get namespaces (subjects)
        stats = index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        
        # Structure to build
        structure = {}
        
        # For each namespace (subject), query to get metadata
        for namespace_name, namespace_info in namespaces.items():
            if namespace_info.get("vector_count", 0) == 0:
                continue
            
            # Query some vectors to get metadata (limit to 1000 to sample)
            # We'll use a dummy vector to query by
            query_response = index.query(
                namespace=namespace_name,
                vector=[0.0] * 768,  # Dummy vector
                top_k=1000,  # Get up to 1000 samples
                include_metadata=True
            )
            
            # Extract unique class/chapter combinations
            classes = {}
            for match in query_response.get("matches", []):
                metadata = match.get("metadata", {})
                
                # Support both old format (class, chapter) and new format (class_level, chapter_number)
                class_level = metadata.get("class_level") or metadata.get("class")
                chapter_number = metadata.get("chapter_number") or metadata.get("chapter")
                
                # Try to extract class number from string like "Class 6" or just "6"
                if class_level:
                    if isinstance(class_level, str):
                        # Extract number from strings like "Class 6" or "6"
                        import re
                        match_num = re.search(r'(\d+)', str(class_level))
                        if match_num:
                            class_level = int(match_num.group(1))
                        else:
                            continue
                    class_level = int(class_level)
                    
                    class_key = str(class_level)
                    if class_key not in classes:
                        classes[class_key] = {
                            "class_level": class_level,
                            "chapters": set(),
                            "vector_count": 0
                        }
                    
                    if chapter_number:
                        # Extract number from chapter (could be "Chapter 1" or just "1")
                        if isinstance(chapter_number, str):
                            import re
                            match_ch = re.search(r'(\d+)', str(chapter_number))
                            if match_ch:
                                chapter_number = int(match_ch.group(1))
                        if isinstance(chapter_number, (int, float)):
                            classes[class_key]["chapters"].add(int(chapter_number))
                    
                    classes[class_key]["vector_count"] += 1
            
            # Convert sets to sorted lists
            for class_key in classes:
                classes[class_key]["chapters"] = sorted(list(classes[class_key]["chapters"]))
            
            # Add to structure
            if classes:
                structure[namespace_name] = {
                    "total_vectors": namespace_info.get("vector_count", 0),
                    "classes": classes
                }
        
        return {
            "success": True,
            "structure": structure,
            "total_namespaces": len(structure)
        }
        
    except Exception as e:
        logger.error(f"❌ Get hierarchical structure failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HIERARCHICAL DELETE ENDPOINTS ====================

@router.delete("/admin/delete-subject/{subject}")
async def delete_subject(subject: str, confirmation: str = Query(...)):
    """
    Delete ALL vectors for a subject (entire namespace).
    Requires typing the subject name as confirmation.
    
    This deletes:
    - All vectors in Pinecone namespace for this subject
    - All book records in MongoDB for this subject
    """
    try:
        # Verify confirmation matches subject
        if confirmation.lower() != subject.lower():
            raise HTTPException(
                status_code=400, 
                detail=f"Confirmation '{confirmation}' does not match subject '{subject}'"
            )
        
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        namespace = subject.lower().replace(' ', '_')
        
        # Get stats before deletion
        stats_before = index.describe_index_stats()
        namespace_info = stats_before.get("namespaces", {}).get(namespace, {})
        vectors_to_delete = namespace_info.get("vector_count", 0)
        
        if vectors_to_delete == 0:
            raise HTTPException(status_code=404, detail=f"No vectors found in namespace '{namespace}'")
        
        # Delete entire namespace in Pinecone
        logger.info(f"🗑️ Deleting namespace '{namespace}' with {vectors_to_delete} vectors...")
        index.delete(delete_all=True, namespace=namespace)
        
        # Delete all books from MongoDB for this subject
        mongo_result = db.books.delete_many({"subject": {"$regex": f"^{subject}$", "$options": "i"}})
        books_deleted = mongo_result.deleted_count
        
        logger.info(f"✅ Deleted subject '{subject}': {vectors_to_delete} vectors, {books_deleted} book records")
        
        return {
            "success": True,
            "message": f"Subject '{subject}' deleted successfully",
            "deleted": {
                "subject": subject,
                "namespace": namespace,
                "vectors_deleted": vectors_to_delete,
                "books_deleted": books_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete subject failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/delete-class/{subject}/{class_level}")
async def delete_class(subject: str, class_level: int, confirmation: str = Query(...)):
    """
    Delete all vectors for a specific class within a subject.
    Requires typing "Class {class_level}" as confirmation.
    
    This deletes:
    - All vectors in Pinecone with matching subject & class_level metadata
    - All book records in MongoDB for this subject and class
    """
    try:
        expected_confirmation = f"Class {class_level}"
        if confirmation != expected_confirmation:
            raise HTTPException(
                status_code=400,
                detail=f"Confirmation '{confirmation}' does not match expected '{expected_confirmation}'"
            )
        
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        namespace = subject.lower().replace(' ', '_')
        
        # Query to find all vector IDs with this class_level
        # We need to query in batches to get all vectors
        all_vector_ids = []
        
        # Query with metadata filter - get up to 10000 vectors
        query_response = index.query(
            namespace=namespace,
            vector=[0.0] * 768,
            top_k=10000,
            include_metadata=True,
            filter={
                "$or": [
                    {"class_level": class_level},
                    {"class_level": str(class_level)},
                    {"class": class_level},
                    {"class": str(class_level)},
                    {"class": f"Class {class_level}"}
                ]
            }
        )
        
        for match in query_response.get("matches", []):
            all_vector_ids.append(match["id"])
        
        vectors_to_delete = len(all_vector_ids)
        
        if vectors_to_delete == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No vectors found for Class {class_level} in {subject}"
            )
        
        # Delete vectors in batches of 1000
        logger.info(f"🗑️ Deleting {vectors_to_delete} vectors for {subject} Class {class_level}...")
        
        for i in range(0, len(all_vector_ids), 1000):
            batch = all_vector_ids[i:i+1000]
            index.delete(ids=batch, namespace=namespace)
            logger.info(f"  ✓ Deleted batch of {len(batch)} vectors")
        
        # Delete books from MongoDB for this subject and class
        mongo_result = db.books.delete_many({
            "subject": {"$regex": f"^{subject}$", "$options": "i"},
            "class_level": class_level
        })
        books_deleted = mongo_result.deleted_count
        
        logger.info(f"✅ Deleted Class {class_level} from {subject}: {vectors_to_delete} vectors, {books_deleted} book records")
        
        return {
            "success": True,
            "message": f"Class {class_level} deleted from {subject}",
            "deleted": {
                "subject": subject,
                "class_level": class_level,
                "vectors_deleted": vectors_to_delete,
                "books_deleted": books_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete class failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/delete-chapter/{subject}/{class_level}/{chapter_number}")
async def delete_chapter(subject: str, class_level: int, chapter_number: int, confirmation: str = Query(...)):
    """
    Delete all vectors for a specific chapter.
    Requires typing "Chapter {chapter_number}" as confirmation.
    
    This deletes:
    - All vectors in Pinecone with matching subject, class_level & chapter_number metadata
    - The book record in MongoDB for this chapter
    """
    try:
        expected_confirmation = f"Chapter {chapter_number}"
        if confirmation != expected_confirmation:
            raise HTTPException(
                status_code=400,
                detail=f"Confirmation '{confirmation}' does not match expected '{expected_confirmation}'"
            )
        
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index = pc.Index(
            name=settings.PINECONE_MASTER_INDEX,
            host=settings.PINECONE_MASTER_HOST
        )
        
        namespace = subject.lower().replace(' ', '_')
        
        # Query to find all vector IDs with this chapter
        all_vector_ids = []
        
        # Query with metadata filter
        query_response = index.query(
            namespace=namespace,
            vector=[0.0] * 768,
            top_k=10000,
            include_metadata=True,
            filter={
                "$and": [
                    {"$or": [
                        {"class_level": class_level},
                        {"class_level": str(class_level)},
                        {"class": class_level},
                        {"class": str(class_level)},
                        {"class": f"Class {class_level}"}
                    ]},
                    {"$or": [
                        {"chapter_number": chapter_number},
                        {"chapter_number": str(chapter_number)},
                        {"chapter": chapter_number},
                        {"chapter": str(chapter_number)},
                        {"chapter": f"Chapter {chapter_number}"}
                    ]}
                ]
            }
        )
        
        for match in query_response.get("matches", []):
            all_vector_ids.append(match["id"])
        
        vectors_to_delete = len(all_vector_ids)
        
        if vectors_to_delete == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No vectors found for {subject} Class {class_level} Chapter {chapter_number}"
            )
        
        # Delete vectors
        logger.info(f"🗑️ Deleting {vectors_to_delete} vectors for {subject} Class {class_level} Chapter {chapter_number}...")
        
        for i in range(0, len(all_vector_ids), 1000):
            batch = all_vector_ids[i:i+1000]
            index.delete(ids=batch, namespace=namespace)
        
        # Delete book record from MongoDB
        mongo_result = db.books.delete_many({
            "subject": {"$regex": f"^{subject}$", "$options": "i"},
            "class_level": class_level,
            "chapter_number": chapter_number
        })
        books_deleted = mongo_result.deleted_count
        
        logger.info(f"✅ Deleted Chapter {chapter_number} from {subject} Class {class_level}: {vectors_to_delete} vectors, {books_deleted} book records")
        
        return {
            "success": True,
            "message": f"Chapter {chapter_number} deleted from {subject} Class {class_level}",
            "deleted": {
                "subject": subject,
                "class_level": class_level,
                "chapter_number": chapter_number,
                "vectors_deleted": vectors_to_delete,
                "books_deleted": books_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete chapter failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
