"""
Support Tickets Router
- Create, view, update support tickets
- Admin can manage all tickets
- Students can create and view their own tickets
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import logging

from app.db.mongo import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/support-tickets", tags=["Support Tickets"])


# ==================== PYDANTIC MODELS ====================

class TicketCreate(BaseModel):
    """Model for creating a support ticket."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(default="general", description="Category: general, technical, content, account, other")
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")


class TicketUpdate(BaseModel):
    """Model for updating a ticket."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # open, in_progress, resolved, closed


class TicketReply(BaseModel):
    """Model for adding a reply to a ticket."""
    message: str = Field(..., min_length=1, max_length=5000)
    is_admin: bool = Field(default=False)
    author_name: str = Field(default="Admin")


class TicketResponse(BaseModel):
    """Response model for a ticket."""
    id: str
    ticket_number: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_by: str
    created_by_name: str
    created_at: str
    updated_at: Optional[str]
    replies: List[dict] = []
    assigned_to: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

def generate_ticket_number() -> str:
    """Generate a unique ticket number."""
    try:
        counter = db.student_counters.find_one_and_update(
            {"_id": "ticket_count"},
            {"$inc": {"count": 1}},
            upsert=True,
            return_document=True
        )
        ticket_num = counter.get("count", 1)
        return f"TKT{ticket_num:05d}"  # TKT00001, TKT00002, etc.
    except Exception as e:
        logger.error(f"Error generating ticket number: {e}")
        import time
        return f"TKT{int(time.time()) % 100000:05d}"


def serialize_ticket(ticket: dict) -> dict:
    """Convert MongoDB document to response dict."""
    return {
        "id": str(ticket.get("_id", "")),
        "ticket_number": ticket.get("ticket_number", ""),
        "title": ticket.get("title", ""),
        "description": ticket.get("description", ""),
        "category": ticket.get("category", "general"),
        "priority": ticket.get("priority", "medium"),
        "status": ticket.get("status", "open"),
        "created_by": ticket.get("created_by", ""),
        "created_by_name": ticket.get("created_by_name", "Unknown"),
        "created_at": ticket.get("created_at", datetime.utcnow()).isoformat() if ticket.get("created_at") else None,
        "updated_at": ticket.get("updated_at").isoformat() if ticket.get("updated_at") else None,
        "replies": ticket.get("replies", []),
        "assigned_to": ticket.get("assigned_to"),
        "is_read_by_admin": ticket.get("is_read_by_admin", False),
        "read_at": ticket.get("read_at").isoformat() if ticket.get("read_at") else None
    }


# ==================== TICKET ENDPOINTS ====================

@router.get("/")
async def get_tickets(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    is_admin: bool = Query(False)
):
    """
    Get list of support tickets.
    - Admin: Can see all tickets
    - User: Can only see their own tickets
    """
    try:
        filter_query = {}
        
        # If not admin, filter by user_id
        if not is_admin and user_id:
            filter_query["created_by"] = user_id
        
        if status:
            filter_query["status"] = status
        
        if category:
            filter_query["category"] = category
        
        if priority:
            filter_query["priority"] = priority
        
        cursor = db.support_tickets.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)
        tickets = [serialize_ticket(t) for t in cursor]
        
        # Get counts
        total_count = db.support_tickets.count_documents(filter_query)
        open_count = db.support_tickets.count_documents({**filter_query, "status": "open"})
        in_progress_count = db.support_tickets.count_documents({**filter_query, "status": "in_progress"})
        resolved_count = db.support_tickets.count_documents({**filter_query, "status": "resolved"})
        
        return {
            "tickets": tickets,
            "total": total_count,
            "open": open_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count
        }
        
    except Exception as e:
        logger.error(f"Error fetching tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_ticket(
    ticket: TicketCreate,
    user_id: str = Query(..., description="ID of the user creating the ticket"),
    user_name: str = Query("Unknown", description="Name of the user")
):
    """
    Create a new support ticket.
    Also creates a notification for admin users.
    """
    try:
        ticket_number = generate_ticket_number()
        
        ticket_doc = {
            "ticket_number": ticket_number,
            "title": ticket.title,
            "description": ticket.description,
            "category": ticket.category,
            "priority": ticket.priority,
            "status": "open",
            "created_by": user_id,
            "created_by_name": user_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "replies": [],
            "assigned_to": None,
            "is_read_by_admin": False
        }
        
        result = db.support_tickets.insert_one(ticket_doc)
        ticket_doc["_id"] = result.inserted_id
        
        # Create notification for admin
        try:
            notification_doc = {
                "type": "support_ticket",
                "title": f"New Support Ticket: {ticket_number}",
                "message": f"{user_name} submitted a new {ticket.priority} priority ticket: {ticket.title}",
                "ticket_id": str(result.inserted_id),
                "ticket_number": ticket_number,
                "category": ticket.category,
                "priority": ticket.priority,
                "for_admin": True,
                "is_read": False,
                "created_at": datetime.utcnow(),
                "created_by": user_id,
                "created_by_name": user_name
            }
            db.notifications.insert_one(notification_doc)
            logger.info(f"Created admin notification for ticket: {ticket_number}")
        except Exception as notif_error:
            logger.error(f"Failed to create notification: {notif_error}")
        
        logger.info(f"Created ticket: {ticket_number} by {user_id}")
        return serialize_ticket(ticket_doc)
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    """
    Get a single ticket by ID or ticket number.
    """
    try:
        # Try by ObjectId
        ticket = None
        if ObjectId.is_valid(ticket_id):
            ticket = db.support_tickets.find_one({"_id": ObjectId(ticket_id)})
        
        # Try by ticket number
        if not ticket:
            ticket = db.support_tickets.find_one({"ticket_number": ticket_id})
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return serialize_ticket(ticket)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: str, ticket: TicketUpdate):
    """
    Update a ticket (admin only).
    """
    try:
        update_doc = {}
        
        if ticket.title is not None:
            update_doc["title"] = ticket.title
        if ticket.description is not None:
            update_doc["description"] = ticket.description
        if ticket.category is not None:
            update_doc["category"] = ticket.category
        if ticket.priority is not None:
            update_doc["priority"] = ticket.priority
        if ticket.status is not None:
            update_doc["status"] = ticket.status
        
        if not update_doc:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_doc["updated_at"] = datetime.utcnow()
        
        # Find and update
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        result = db.support_tickets.find_one_and_update(
            query,
            {"$set": update_doc},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        logger.info(f"Updated ticket: {ticket_id}")
        return serialize_ticket(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/reply")
async def add_reply(ticket_id: str, reply: TicketReply):
    """
    Add a reply to a ticket.
    Creates notification for the appropriate party (admin reply -> student, student reply -> admin).
    """
    try:
        # First get the ticket to know who to notify
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        ticket = db.support_tickets.find_one(query)
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        reply_doc = {
            "id": str(ObjectId()),
            "message": reply.message,
            "is_admin": reply.is_admin,
            "author_name": reply.author_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        update_fields = {
            "updated_at": datetime.utcnow()
        }
        
        # If admin replies, mark as read by admin and update status
        if reply.is_admin:
            update_fields["is_read_by_admin"] = True
            update_fields["status"] = "in_progress"
        
        result = db.support_tickets.find_one_and_update(
            query,
            {
                "$push": {"replies": reply_doc},
                "$set": update_fields
            },
            return_document=True
        )
        
        # Create notification
        try:
            if reply.is_admin:
                # Admin replied -> Notify student
                notification_doc = {
                    "type": "ticket_reply",
                    "title": f"Reply to your ticket {ticket.get('ticket_number', '')}",
                    "message": f"Admin replied to your support ticket: {ticket.get('title', '')}",
                    "ticket_id": str(ticket["_id"]),
                    "ticket_number": ticket.get("ticket_number", ""),
                    "user_id": ticket.get("created_by"),  # Student who created the ticket
                    "for_admin": False,
                    "is_read": False,
                    "created_at": datetime.utcnow()
                }
            else:
                # Student replied -> Notify admin
                notification_doc = {
                    "type": "ticket_reply",
                    "title": f"New reply on ticket {ticket.get('ticket_number', '')}",
                    "message": f"{reply.author_name} replied to ticket: {ticket.get('title', '')}",
                    "ticket_id": str(ticket["_id"]),
                    "ticket_number": ticket.get("ticket_number", ""),
                    "for_admin": True,
                    "is_read": False,
                    "created_at": datetime.utcnow()
                }
            
            db.notifications.insert_one(notification_doc)
            logger.info(f"Created notification for ticket reply: {ticket_id}")
        except Exception as notif_error:
            logger.error(f"Failed to create reply notification: {notif_error}")
        
        logger.info(f"Added reply to ticket: {ticket_id}")
        return serialize_ticket(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding reply: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str):
    """
    Delete a ticket (admin only).
    """
    try:
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        result = db.support_tickets.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        logger.info(f"Deleted ticket: {ticket_id}")
        return {"success": True, "message": "Ticket deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/close")
async def close_ticket(ticket_id: str):
    """
    Close a ticket.
    """
    try:
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        result = db.support_tickets.find_one_and_update(
            query,
            {"$set": {"status": "closed", "updated_at": datetime.utcnow()}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        logger.info(f"Closed ticket: {ticket_id}")
        return serialize_ticket(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str):
    """
    Mark a ticket as resolved.
    """
    try:
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        result = db.support_tickets.find_one_and_update(
            query,
            {"$set": {"status": "resolved", "updated_at": datetime.utcnow()}},
            return_document=True
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Notify student that ticket is resolved
        try:
            notification_doc = {
                "type": "ticket_resolved",
                "title": f"Ticket {result.get('ticket_number', '')} Resolved",
                "message": f"Your support ticket '{result.get('title', '')}' has been marked as resolved.",
                "ticket_id": str(result["_id"]),
                "ticket_number": result.get("ticket_number", ""),
                "user_id": result.get("created_by"),
                "for_admin": False,
                "is_read": False,
                "created_at": datetime.utcnow()
            }
            db.notifications.insert_one(notification_doc)
        except Exception as notif_error:
            logger.error(f"Failed to create resolve notification: {notif_error}")
        
        logger.info(f"Resolved ticket: {ticket_id}")
        return serialize_ticket(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ticket_id}/mark-read")
async def mark_ticket_read(ticket_id: str, by_admin: bool = Query(True)):
    """
    Mark a ticket as read by admin.
    Creates a notification for the student that their ticket has been seen.
    """
    try:
        query = {"_id": ObjectId(ticket_id)} if ObjectId.is_valid(ticket_id) else {"ticket_number": ticket_id}
        ticket = db.support_tickets.find_one(query)
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Update ticket
        result = db.support_tickets.find_one_and_update(
            query,
            {"$set": {"is_read_by_admin": True, "read_at": datetime.utcnow()}},
            return_document=True
        )
        
        # Notify student that admin has seen their ticket
        if by_admin and not ticket.get("is_read_by_admin"):
            try:
                notification_doc = {
                    "type": "ticket_read",
                    "title": f"Ticket {ticket.get('ticket_number', '')} Viewed",
                    "message": f"Admin has viewed your support ticket: {ticket.get('title', '')}",
                    "ticket_id": str(ticket["_id"]),
                    "ticket_number": ticket.get("ticket_number", ""),
                    "user_id": ticket.get("created_by"),
                    "for_admin": False,
                    "is_read": False,
                    "created_at": datetime.utcnow()
                }
                db.notifications.insert_one(notification_doc)
                logger.info(f"Created read notification for ticket: {ticket_id}")
            except Exception as notif_error:
                logger.error(f"Failed to create read notification: {notif_error}")
        
        return serialize_ticket(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking ticket as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS ENDPOINTS ====================

@router.get("/stats/summary")
async def get_ticket_stats():
    """
    Get ticket statistics for admin dashboard.
    """
    try:
        total = db.support_tickets.count_documents({})
        open_tickets = db.support_tickets.count_documents({"status": "open"})
        in_progress = db.support_tickets.count_documents({"status": "in_progress"})
        resolved = db.support_tickets.count_documents({"status": "resolved"})
        closed = db.support_tickets.count_documents({"status": "closed"})
        
        # Priority breakdown
        high_priority = db.support_tickets.count_documents({"priority": {"$in": ["high", "urgent"]}, "status": {"$in": ["open", "in_progress"]}})
        
        # Category breakdown
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = list(db.support_tickets.aggregate(category_pipeline))
        
        return {
            "total": total,
            "open": open_tickets,
            "in_progress": in_progress,
            "resolved": resolved,
            "closed": closed,
            "high_priority": high_priority,
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Error getting ticket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NOTIFICATION ENDPOINTS ====================

@router.get("/notifications/admin")
async def get_admin_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False)
):
    """
    Get notifications for admin (new tickets, student replies).
    """
    try:
        filter_query = {"for_admin": True}
        if unread_only:
            filter_query["is_read"] = False
        
        notifications = list(db.notifications.find(filter_query).sort("created_at", -1).limit(limit))
        
        result = []
        for n in notifications:
            result.append({
                "id": str(n["_id"]),
                "type": n.get("type", ""),
                "title": n.get("title", ""),
                "message": n.get("message", ""),
                "ticket_id": n.get("ticket_id"),
                "ticket_number": n.get("ticket_number"),
                "is_read": n.get("is_read", False),
                "created_at": n.get("created_at").isoformat() if n.get("created_at") else None,
                "created_by_name": n.get("created_by_name", "")
            })
        
        unread_count = db.notifications.count_documents({"for_admin": True, "is_read": False})
        
        return {
            "notifications": result,
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"Error getting admin notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/user/{user_id}")
async def get_user_notifications(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False)
):
    """
    Get notifications for a specific user (admin replies, ticket status updates).
    """
    try:
        filter_query = {"user_id": user_id, "for_admin": False}
        if unread_only:
            filter_query["is_read"] = False
        
        notifications = list(db.notifications.find(filter_query).sort("created_at", -1).limit(limit))
        
        result = []
        for n in notifications:
            result.append({
                "id": str(n["_id"]),
                "type": n.get("type", ""),
                "title": n.get("title", ""),
                "message": n.get("message", ""),
                "ticket_id": n.get("ticket_id"),
                "ticket_number": n.get("ticket_number"),
                "is_read": n.get("is_read", False),
                "created_at": n.get("created_at").isoformat() if n.get("created_at") else None
            })
        
        unread_count = db.notifications.count_documents({"user_id": user_id, "for_admin": False, "is_read": False})
        
        return {
            "notifications": result,
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"Error getting user notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str):
    """
    Mark a notification as read.
    """
    try:
        result = db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    user_id: Optional[str] = None,
    is_admin: bool = Query(False)
):
    """
    Mark all notifications as read for a user or admin.
    """
    try:
        if is_admin:
            filter_query = {"for_admin": True}
        else:
            filter_query = {"user_id": user_id, "for_admin": False}
        
        result = db.notifications.update_many(
            filter_query,
            {"$set": {"is_read": True, "read_at": datetime.utcnow()}}
        )
        
        return {"success": True, "marked_count": result.modified_count}
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
