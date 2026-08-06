from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

from app.constants.order_status import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    selected_attributes: Optional[str] = None  # JSON string of selected attribute options


class OrderCreate(BaseModel):
    full_name: str
    phone_number: str
    district: str
    address: str
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
