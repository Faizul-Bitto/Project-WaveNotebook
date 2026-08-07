from pydantic import BaseModel
from typing import Optional


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    selected_attributes: Optional[str] = None  # JSON string of selected attribute options like {"Size": "XL", "Color": "Red"}


class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None
    selected_attributes: Optional[str] = None
