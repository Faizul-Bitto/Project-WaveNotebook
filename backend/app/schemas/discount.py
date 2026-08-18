from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, model_validator


class BundleSlabSchema(BaseModel):
    min_quantity: int = Field(..., ge=1)
    value_type: str = Field(..., pattern=r"^(percentage|flat)$")
    value: float = Field(..., ge=0)


class BogoRuleSchema(BaseModel):
    product_id: Optional[int] = Field(None, gt=0)
    product_ids: Optional[List[int]] = None
    buy_quantity: int = Field(..., ge=1)
    get_quantity: int = Field(..., ge=1)
    get_discount_percent: float = Field(..., ge=0, le=100)

    @model_validator(mode='after')
    def validate_product_scope(self):
        if not self.product_ids and not self.product_id:
            raise ValueError('Either product_id or product_ids must be provided.')
        return self


class SpendBasedSlabSchema(BaseModel):
    min_spend_amount: float = Field(..., ge=0)
    value_type: str = Field(..., pattern=r"^(percentage|flat)$")
    value: float = Field(..., ge=0)


class SpendBasedRuleSchema(BaseModel):
    scope_type: str = Field(..., pattern=r"^(storewide|category|product)$")
    scope_id: Optional[int] = Field(None, gt=0)
    slabs: List[SpendBasedSlabSchema]


class DiscountScopeSchema(BaseModel):
    scope_type: str = Field(..., pattern=r"^(product|category)$")
    scope_id: int = Field(..., gt=0)


class DiscountCreate(BaseModel):
    name: str
    type: str = Field(..., pattern=r"^(percentage|flat|bundle|bogo|free_shipping|spend_based)$")
    value_type: Optional[str] = Field(None, pattern=r"^(percentage|flat)$")
    value: Optional[float] = Field(None, ge=0)
    max_discount_cap: Optional[float] = Field(None, ge=0)
    free_shipping: Optional[bool] = False

    scope_type: Optional[str] = Field(None, pattern=r"^(product|category)$")
    scope_ids: Optional[List[int]] = Field(None, description="Multiple product/category IDs for this discount")

    bundle_type: Optional[str] = Field(None, pattern=r"^(quantity|combo)$")
    bundle_slabs: Optional[List[BundleSlabSchema]] = None
    required_products: Optional[str] = None

    bogo: Optional[BogoRuleSchema] = None

    spend_based: Optional[SpendBasedRuleSchema] = None

    start_date: datetime
    end_date: Optional[datetime] = None


class DiscountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = Field(None, pattern=r"^(percentage|flat|bundle|bogo|free_shipping|spend_based)$")
    value_type: Optional[str] = Field(None, pattern=r"^(percentage|flat)$")
    value: Optional[float] = Field(None, ge=0)
    max_discount_cap: Optional[float] = Field(None, ge=0)
    free_shipping: Optional[bool] = False

    scope_type: Optional[str] = Field(None, pattern=r"^(product|category)$")
    scope_ids: Optional[List[int]] = Field(None, description="Multiple product/category IDs for this discount")

    bundle_type: Optional[str] = Field(None, pattern=r"^(quantity|combo)$")
    bundle_slabs: Optional[List[BundleSlabSchema]] = None
    required_products: Optional[str] = None

    bogo: Optional[BogoRuleSchema] = None

    spend_based: Optional[SpendBasedRuleSchema] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern=r"^(active|inactive)$")
