from pydantic import BaseModel
from typing import Optional


class AttributeCreate(BaseModel):
    name: str


class AttributeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
