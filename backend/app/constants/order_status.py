"""
Order status enum for dropdown selection.
"""

from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CALLED = "called"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# All valid statuses for frontend dropdown
ORDER_STATUSES = [
    {"value": "pending", "label": "Pending"},
    {"value": "called", "label": "Called"},
    {"value": "confirmed", "label": "Confirmed"},
    {"value": "processing", "label": "Processing"},
    {"value": "shipped", "label": "Shipped"},
    {"value": "delivered", "label": "Delivered"},
    {"value": "cancelled", "label": "Cancelled"},
]