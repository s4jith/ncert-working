"""
Test Management Router
- Admin creates tests for specific class/subject
- PDF upload for test questions
- Optional timing (start/end dates)
- Student notifications
- Test submissions (PDF) from students
- Admin feedback/comments
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import os
import uuid
import logging
import shutil

from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tests", tags=["Test Management"])

# Directory for storing uploaded test PDFs
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "tests")
SUBMISSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "submissions")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SUBMISSION_DIR, exist_ok=True)


# ==================== PYDANTIC MODELS ====================

class TestCreate(BaseModel):
    """Model for creating a test."""
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    class_level: int = Field(..., ge=5, le=12)
    subject: str = Field(...)
    is_timed: bool = Field(default=False)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None  # For timed tests during attempt


class TestUpdate(BaseModel):
    """Model for updating a test."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_timed: Optional[bool] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class TestResponse(BaseModel):
    """Model for test response."""
    id: str
    title: str
    description: Optional[str]
    class_level: int
    subject: str
    pdf_filename: str
    pdf_url: str
    is_timed: bool
    start_datetime: Optional[str]
    end_datetime: Optional[str]
    duration_minutes: Optional[int]
    is_active: bool
    created_by: str
    created_at: str
    submission_count: int = 0
    status: str  # upcoming, active, closed


class SubmissionCreate(BaseModel):
    """Model for test submission."""
    test_id: str
    student_id: str


class CommentCreate(BaseModel):
    """Model for adding comment to submission."""
    comment: str = Field(..., min_length=1)


# ==================== HELPER FUNCTIONS ====================

def serialize_test(test: dict) -> dict:
    """Convert MongoDB document to response dict."""
    now = datetime.utcnow()
    
    # Determine test status
    status = "active"
    if test.get("is_timed"):
        start = test.get("start_datetime")
        end = test.get("end_datetime")
        if start and start > now:
            status = "upcoming"
        elif end and end < now:
            status = "closed"
    
    if not test.get("is_active", True):
        status = "closed"
    
    return {
        "id": str(test.get("_id", "")),
        "title": test.get("title", ""),
        "description": test.get("description", ""),
        "class_level": test.get("class_level", 10),
        "subject": test.get("subject", ""),
        "pdf_filename": test.get("pdf_filename", ""),
        "pdf_url": f"/api/tests/pdf/{test.get('pdf_filename', '')}",
        "is_timed": test.get("is_timed", False),
        "start_datetime": test.get("start_datetime").isoformat() if test.get("start_datetime") else None,
        "end_datetime": test.get("end_datetime").isoformat() if test.get("end_datetime") else None,
        "duration_minutes": test.get("duration_minutes"),
        "is_active": test.get("is_active", True),
        "created_by": test.get("created_by", ""),
        "created_at": test.get("created_at", datetime.utcnow()).isoformat(),
        "submission_count": test.get("submission_count", 0),
        "status": status
    }


def serialize_submission(submission: dict) -> dict:
    """Convert MongoDB submission document to response dict."""
    return {
        "id": str(submission.get("_id", "")),
        "test_id": str(submission.get("test_id", "")),
        "test_title": submission.get("test_title", ""),
        "student_id": str(submission.get("student_id", "")),
        "student_name": submission.get("student_name", ""),
        "student_user_id": submission.get("student_user_id", ""),
        "pdf_filename": submission.get("pdf_filename", ""),
        "pdf_url": f"/api/tests/submission-pdf/{submission.get('pdf_filename', '')}",
        "submitted_at": submission.get("submitted_at", datetime.utcnow()).isoformat(),
        "admin_comment": submission.get("admin_comment", ""),
        "comment_at": submission.get("comment_at").isoformat() if submission.get("comment_at") else None,
        "is_reviewed": submission.get("is_reviewed", False)
    }


# ==================== TEST CRUD ENDPOINTS ====================

@router.post("/create")
async def create_test(
    title: str = Form(...),
    description: str = Form(None),
    class_level: int = Form(...),
    subject: str = Form(...),
    is_timed: bool = Form(False),
    start_datetime: str = Form(None),
    end_datetime: str = Form(None),
    duration_minutes: int = Form(None),
    created_by: str = Form("admin"),
    pdf_file: UploadFile = File(...)
):
    """
    Create a new test with PDF upload.
    Notifies all students of the specified class.
    """
    try:
        # Validate PDF file
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}_{pdf_file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_datetime and start_datetime != "null" and start_datetime != "":
            try:
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                start_dt = datetime.strptime(start_datetime[:19], "%Y-%m-%dT%H:%M:%S")
        
        if end_datetime and end_datetime != "null" and end_datetime != "":
            try:
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                end_dt = datetime.strptime(end_datetime[:19], "%Y-%m-%dT%H:%M:%S")
        
        # Create test document
        test_doc = {
            "title": title,
            "description": description,
            "class_level": class_level,
            "subject": subject,
            "pdf_filename": unique_filename,
            "is_timed": is_timed,
            "start_datetime": start_dt,
            "end_datetime": end_dt,
            "duration_minutes": duration_minutes,
            "is_active": True,
            "created_by": created_by,
            "created_at": datetime.utcnow(),
            "submission_count": 0
        }
        
        # Insert into database
        result = db.tests.insert_one(test_doc)
        test_doc["_id"] = result.inserted_id
        
        # Create notifications for all students in this class
        students = list(db.users.find({
            "role": "student",
            "class_level": class_level,
            "is_active": True
        }))
        
        notifications = []
        for student in students:
            notifications.append({
                "user_id": str(student["_id"]),
                "type": "new_test",
                "title": "New Test Available",
                "message": f"A new {subject} test '{title}' has been created for Class {class_level}.",
                "test_id": str(result.inserted_id),
                "is_read": False,
                "created_at": datetime.utcnow()
            })
        
        if notifications:
            db.notifications.insert_many(notifications)
            logger.info(f"Created {len(notifications)} notifications for test {title}")
        
        logger.info(f"Created test: {title} for Class {class_level} - {subject}")
        
        return {
            "success": True,
            "message": f"Test created successfully! {len(students)} students notified.",
            "test": serialize_test(test_doc),
            "students_notified": len(students)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin")
async def get_admin_tests(
    class_level: Optional[int] = None,
    subject: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Get all tests for admin view.
    Can filter by class, subject, status.
    """
    try:
        query = {}
        if class_level:
            query["class_level"] = class_level
        if subject:
            query["subject"] = subject
        
        tests = list(db.tests.find(query).sort("created_at", -1).skip(skip).limit(limit))
        
        result = [serialize_test(t) for t in tests]
        
        # Filter by status if provided
        if status:
            result = [t for t in result if t["status"] == status]
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching admin tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{student_id}")
async def get_student_tests(
    student_id: str,
    status: Optional[str] = None
):
    """
    Get all tests available for a specific student based on their class level.
    Also includes submission status for each test.
    """
    try:
        # Get student's class level
        query = {"_id": ObjectId(student_id)} if ObjectId.is_valid(student_id) else {"user_id": student_id}
        student = db.users.find_one(query)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        class_level = student.get("class_level", 10)
        
        # Get tests for this class
        tests = list(db.tests.find({
            "class_level": class_level,
            "is_active": True
        }).sort("created_at", -1))
        
        # Get student's submissions
        submissions = list(db.test_submissions.find({
            "student_id": str(student["_id"])
        }))
        submitted_test_ids = {str(s.get("test_id")): s for s in submissions}
        
        result = []
        for test in tests:
            test_data = serialize_test(test)
            test_id = str(test["_id"])
            
            # Add submission info
            if test_id in submitted_test_ids:
                sub = submitted_test_ids[test_id]
                test_data["has_submitted"] = True
                test_data["submission_id"] = str(sub["_id"])
                test_data["submission_date"] = sub.get("submitted_at").isoformat() if sub.get("submitted_at") else None
                test_data["has_feedback"] = bool(sub.get("admin_comment"))
            else:
                test_data["has_submitted"] = False
                test_data["submission_id"] = None
                test_data["submission_date"] = None
                test_data["has_feedback"] = False
            
            result.append(test_data)
        
        # Filter by status if provided
        if status:
            result = [t for t in result if t["status"] == status]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student tests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}")
async def get_test(test_id: str):
    """Get a specific test by ID."""
    try:
        query = {"_id": ObjectId(test_id)} if ObjectId.is_valid(test_id) else {"title": test_id}
        test = db.tests.find_one(query)
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        return serialize_test(test)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{test_id}")
async def update_test(test_id: str, test: TestUpdate):
    """Update a test."""
    try:
        update_doc = {}
        if test.title is not None:
            update_doc["title"] = test.title
        if test.description is not None:
            update_doc["description"] = test.description
        if test.is_timed is not None:
            update_doc["is_timed"] = test.is_timed
        if test.start_datetime is not None:
            update_doc["start_datetime"] = test.start_datetime
        if test.end_datetime is not None:
            update_doc["end_datetime"] = test.end_datetime
        if test.duration_minutes is not None:
            update_doc["duration_minutes"] = test.duration_minutes
        if test.is_active is not None:
            update_doc["is_active"] = test.is_active
        
        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_doc["updated_at"] = datetime.utcnow()
        
        result = db.tests.find_one_and_update(
            {"_id": ObjectId(test_id)},
            {"$set": update_doc},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Test not found")
        
        return serialize_test(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{test_id}")
async def delete_test(test_id: str):
    """Delete a test and its PDF file."""
    try:
        test = db.tests.find_one({"_id": ObjectId(test_id)})
        
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Delete PDF file
        pdf_path = os.path.join(UPLOAD_DIR, test.get("pdf_filename", ""))
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        # Delete test document
        db.tests.delete_one({"_id": ObjectId(test_id)})
        
        # Delete related notifications
        db.notifications.delete_many({"test_id": test_id})
        
        logger.info(f"Deleted test: {test_id}")
        
        return {"success": True, "message": "Test deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PDF SERVING ENDPOINTS ====================

from fastapi.responses import FileResponse

@router.get("/pdf/{filename}")
async def get_test_pdf(filename: str):
    """Serve test PDF file."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


@router.get("/submission-pdf/{filename}")
async def get_submission_pdf(filename: str):
    """Serve submission PDF file."""
    file_path = os.path.join(SUBMISSION_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


# ==================== SUBMISSION ENDPOINTS ====================

@router.post("/submit")
async def submit_test(
    test_id: str = Form(...),
    student_id: str = Form(...),
    pdf_file: UploadFile = File(...)
):
    """
    Student submits their test answers as PDF.
    """
    try:
        # Validate PDF
        if not pdf_file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Verify test exists
        test = db.tests.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Verify student exists
        query = {"_id": ObjectId(student_id)} if ObjectId.is_valid(student_id) else {"user_id": student_id}
        student = db.users.find_one(query)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Check if already submitted
        existing = db.test_submissions.find_one({
            "test_id": test_id,
            "student_id": str(student["_id"])
        })
        if existing:
            raise HTTPException(status_code=400, detail="You have already submitted this test")
        
        # Check if test is still open
        if test.get("is_timed"):
            now = datetime.utcnow()
            end_dt = test.get("end_datetime")
            if end_dt and end_dt < now:
                raise HTTPException(status_code=400, detail="Test submission period has ended")
        
        # Save submission PDF
        unique_filename = f"{test_id}_{student['user_id']}_{uuid.uuid4()}.pdf"
        file_path = os.path.join(SUBMISSION_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)
        
        # Create submission document
        submission_doc = {
            "test_id": test_id,
            "test_title": test.get("title", ""),
            "student_id": str(student["_id"]),
            "student_name": student.get("name", ""),
            "student_user_id": student.get("user_id", ""),
            "pdf_filename": unique_filename,
            "submitted_at": datetime.utcnow(),
            "admin_comment": "",
            "comment_at": None,
            "is_reviewed": False
        }
        
        result = db.test_submissions.insert_one(submission_doc)
        submission_doc["_id"] = result.inserted_id
        
        # Update test submission count
        db.tests.update_one(
            {"_id": ObjectId(test_id)},
            {"$inc": {"submission_count": 1}}
        )
        
        # Create notification for admin
        db.notifications.insert_one({
            "user_id": "admin",
            "type": "test_submission",
            "title": "New Test Submission",
            "message": f"{student.get('name')} submitted '{test.get('title')}'",
            "test_id": test_id,
            "submission_id": str(result.inserted_id),
            "is_read": False,
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"Student {student.get('user_id')} submitted test {test_id}")
        
        return {
            "success": True,
            "message": "Test submitted successfully!",
            "submission": serialize_submission(submission_doc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions/{test_id}")
async def get_test_submissions(test_id: str):
    """
    Get all submissions for a specific test (admin view).
    """
    try:
        submissions = list(db.test_submissions.find({"test_id": test_id}).sort("submitted_at", -1))
        return [serialize_submission(s) for s in submissions]
        
    except Exception as e:
        logger.error(f"Error fetching submissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-submissions/{student_id}")
async def get_student_submissions(student_id: str):
    """
    Get all submissions by a student.
    """
    try:
        query = {"_id": ObjectId(student_id)} if ObjectId.is_valid(student_id) else {"user_id": student_id}
        student = db.users.find_one(query)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        submissions = list(db.test_submissions.find({
            "student_id": str(student["_id"])
        }).sort("submitted_at", -1))
        
        return [serialize_submission(s) for s in submissions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student submissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FEEDBACK/COMMENT ENDPOINTS ====================

@router.post("/submissions/{submission_id}/comment")
async def add_comment(submission_id: str, comment_data: CommentCreate):
    """
    Admin adds a comment/feedback to a student's submission.
    Creates notification for the student.
    """
    try:
        submission = db.test_submissions.find_one({"_id": ObjectId(submission_id)})
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Update submission with comment
        db.test_submissions.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "admin_comment": comment_data.comment,
                    "comment_at": datetime.utcnow(),
                    "is_reviewed": True
                }
            }
        )
        
        # Create notification for student
        db.notifications.insert_one({
            "user_id": submission.get("student_id"),
            "type": "test_feedback",
            "title": "Test Feedback Received",
            "message": f"You have received feedback on '{submission.get('test_title')}'",
            "test_id": submission.get("test_id"),
            "submission_id": submission_id,
            "is_read": False,
            "created_at": datetime.utcnow()
        })
        
        logger.info(f"Added comment to submission {submission_id}")
        
        return {
            "success": True,
            "message": "Comment added and student notified!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/submission/{submission_id}")
async def get_submission(submission_id: str):
    """Get a specific submission."""
    try:
        submission = db.test_submissions.find_one({"_id": ObjectId(submission_id)})
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        return serialize_submission(submission)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching submission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NOTIFICATION ENDPOINTS ====================

@router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50
):
    """Get notifications for a user."""
    try:
        query = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        
        notifications = list(db.notifications.find(query).sort("created_at", -1).limit(limit))
        
        return [{
            "id": str(n["_id"]),
            "type": n.get("type", ""),
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "test_id": n.get("test_id"),
            "submission_id": n.get("submission_id"),
            "is_read": n.get("is_read", False),
            "created_at": n.get("created_at", datetime.utcnow()).isoformat()
        } for n in notifications]
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read."""
    try:
        result = db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{user_id}/read-all")
async def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read for a user."""
    try:
        result = db.notifications.update_many(
            {"user_id": user_id, "is_read": False},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        return {"success": True, "marked_read": result.modified_count}
        
    except Exception as e:
        logger.error(f"Error marking all notifications read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS ENDPOINTS ====================

@router.get("/stats/overview")
async def get_test_stats():
    """Get overall test statistics for admin dashboard."""
    try:
        total_tests = db.tests.count_documents({})
        active_tests = db.tests.count_documents({"is_active": True})
        total_submissions = db.test_submissions.count_documents({})
        reviewed_submissions = db.test_submissions.count_documents({"is_reviewed": True})
        pending_review = total_submissions - reviewed_submissions
        
        # Tests by class
        pipeline = [
            {"$group": {"_id": "$class_level", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        tests_by_class = list(db.tests.aggregate(pipeline))
        
        # Tests by subject
        pipeline = [
            {"$group": {"_id": "$subject", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        tests_by_subject = list(db.tests.aggregate(pipeline))
        
        return {
            "total_tests": total_tests,
            "active_tests": active_tests,
            "total_submissions": total_submissions,
            "pending_review": pending_review,
            "reviewed_submissions": reviewed_submissions,
            "tests_by_class": [{"class_level": t["_id"], "count": t["count"]} for t in tests_by_class],
            "tests_by_subject": [{"subject": t["_id"], "count": t["count"]} for t in tests_by_subject]
        }
        
    except Exception as e:
        logger.error(f"Error fetching test stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
