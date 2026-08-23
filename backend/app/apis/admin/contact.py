from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import desc
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.contact import Contact

router = APIRouter(
    prefix="/admin/contacts",
    tags=["Admin - Contacts"],
)


@router.get("/unread-count", status_code=status.HTTP_200_OK)
async def get_unread_count(db: db_dependency, admin: admin_dependency):
    """
    Get the number of unread contact messages.
    Used by the admin panel badge (polled for near real-time updates).
    GET /admin/contacts/unread-count
    """
    try:
        count = db.query(Contact).filter(Contact.is_read == False).count()  # noqa: E712
        return {"count": count}
    except Exception as e:
        logger.error(f"❌ Error counting unread contacts | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count unread messages.",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_contacts(
    db: db_dependency,
    admin: admin_dependency,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    filter: str = Query("all", pattern="^(all|unread|read)$"),
):
    """
    List contact messages with optional read/unread filtering.
    GET /admin/contacts?skip=0&limit=20&filter=all
    """
    try:
        query = db.query(Contact)
        if filter == "unread":
            query = query.filter(Contact.is_read == False)  # noqa: E712
        elif filter == "read":
            query = query.filter(Contact.is_read == True)  # noqa: E712

        total = query.count()
        messages = (
            query.order_by(desc(Contact.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {
            "total": total,
            "messages": [
                {
                    "id": m.id,
                    "name": m.name,
                    "email": m.email,
                    "phone_number": m.phone_number,
                    "subject": m.subject,
                    "message": m.message,
                    "is_read": m.is_read,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving contacts | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages.",
        )


@router.patch("/{contact_id}/read", status_code=status.HTTP_200_OK)
async def mark_as_read(
    db: db_dependency, admin: admin_dependency, contact_id: int
):
    """
    Mark a contact message as read.
    PATCH /admin/contacts/{id}/read
    """
    try:
        message = db.query(Contact).filter(Contact.id == contact_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found.",
            )

        if not message.is_read:
            message.is_read = True
            db.commit()
            logger.info(f"✅ Contact Message Marked Read | ID={contact_id} | Admin={admin.phone_number}")

        return {"message": "Message marked as read.", "id": message.id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error marking contact read | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark message as read.",
        )


@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
async def delete_contact(
    db: db_dependency, admin: admin_dependency, contact_id: int
):
    """
    Delete a contact message.
    DELETE /admin/contacts/{id}
    """
    try:
        message = db.query(Contact).filter(Contact.id == contact_id).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found.",
            )

        db.delete(message)
        db.commit()
        logger.info(f"🗑️ Contact Message Deleted | ID={contact_id} | Admin={admin.phone_number}")

        return {"message": "Message deleted successfully.", "id": contact_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting contact | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message.",
        )
