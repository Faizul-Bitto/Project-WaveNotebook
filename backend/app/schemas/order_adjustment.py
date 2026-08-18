from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class OrderAdjustmentCreate(BaseModel):
    """Payload for admin to manually adjust an order's total."""
    adjustment_type: str = Field(
        default="manual_discount",
        description="manual_discount (reduce) | manual_charge (increase) | rounding",
    )
    # 'flat' = fixed BDT amount, 'percentage' = % of current order total
    value_type: str = Field(
        default="flat",
        description="flat | percentage",
        pattern=r"^(flat|percentage)$",
    )
    value: Decimal = Field(..., gt=0, description="Adjustment value (BDT amount or percentage)")
    reason: Optional[str] = Field(None, description="Why the admin made this adjustment")