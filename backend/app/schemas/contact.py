from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


class ContactCreate(BaseModel):
    """Payload sent by the public contact form."""

    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone_number: str = Field(..., min_length=6, max_length=20)
    message: str = Field(..., min_length=5)


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: Optional[str] = None
    phone_number: str
    subject: Optional[str] = None
    message: str
    is_read: bool
    created_at: Optional[str] = None
