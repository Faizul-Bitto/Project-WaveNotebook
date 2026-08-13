from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class AttributeOptionCreate(BaseModel):
    attribute_id: int
    value: str


class AttributeOptionUpdate(BaseModel):
    value: Optional[str] = None
