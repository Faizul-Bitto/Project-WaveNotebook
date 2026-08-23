from fastapi import APIRouter, HTTPException
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.contact import Contact
from app.schemas.contact import ContactCreate

router = APIRouter(
    prefix="/contact",
    tags=["Contact"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_contact_message(db: db_dependency, payload: ContactCreate):
    """
    Receive a contact/message submission from the public site.
    POST /contact
    """
    try:
        # Simple length-based spam guard
        if len(payload.message) > 5000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message is too long.",
            )

        new_message = Contact(
            name=payload.name.strip(),
            email=str(payload.email).strip() if payload.email else None,
            phone_number=payload.phone_number.strip(),
            subject="Contact Form Message",
            message=payload.message.strip(),
            is_read=False,
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)

        logger.info(
            f"📩 New Contact Message | ID={new_message.id} | "
            f"Name={new_message.name} | Phone={new_message.phone_number}"
        )

        return {
            "message": "Your message has been sent successfully. We will get back to you soon!",
            "id": new_message.id,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error saving contact message | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send your message.",
        )
