from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

from app.constants.order_status import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: Optional[int] = None  # None when product was deleted (snapshot fallback)
    quantity: int = 1
    selected_attributes: Optional[str] = None  # JSON string of selected attribute options


class OrderCreate(BaseModel):
    full_name: str
    phone_number: str
    email: Optional[str] = None
    district: str
    thana: Optional[str] = ""
    note: Optional[str] = None
    address: str
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
