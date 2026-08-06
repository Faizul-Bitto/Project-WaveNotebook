from pydantic import BaseModel
from typing import Optional


class CartItemCreate(BaseModel):
    phone_number: str
    product_id: int
    quantity: int = 1
    selected_attributes: Optional[str] = None  # JSON string of selected attribute options


class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    selected_attributes: Optional[str] = None