from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal


class ProductCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    specifications: Optional[str] = None
    base_price: Decimal
    is_in_stock: bool = True
    is_active: bool = True
    attributes: List[int]


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[str] = None
    base_price: Optional[Decimal] = None
    is_in_stock: Optional[bool] = None
    is_active: Optional[bool] = None
    attributes: Optional[List[int]] = None
