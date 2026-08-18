from pydantic import BaseModel, Field


class ShippingChargeCreate(BaseModel):
    zone_name: str = Field(..., min_length=1, max_length=255)
    amount: int = Field(..., ge=0)
    is_active: bool = True


class ShippingChargeUpdate(BaseModel):
    zone_name: str = Field(None, min_length=1, max_length=255)
    amount: int = Field(None, ge=0)
    is_active: bool = None
