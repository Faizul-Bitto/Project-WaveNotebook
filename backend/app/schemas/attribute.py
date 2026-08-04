# app/schemas/attribute.py
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal


class AttributeOptionCreate(BaseModel):
    value: str
    additional_price: Decimal = 0


class AttributeOptionUpdate(BaseModel):
    value: Optional[str] = None
    additional_price: Optional[Decimal] = None


class AttributeCreate(BaseModel):
    name: str


class AttributeUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
