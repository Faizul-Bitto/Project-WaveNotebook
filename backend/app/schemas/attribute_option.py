from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class AttributeOptionCreate(BaseModel):
    value: str
    additional_price: Decimal = 0


class AttributeOptionUpdate(BaseModel):
    value: Optional[str] = None
    additional_price: Optional[Decimal] = None
