from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date


class ExpenseTypeBase(BaseModel):
    name: str
    description: Optional[str] = None


class ExpenseTypeCreate(ExpenseTypeBase):
    pass


class ExpenseTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ExpenseTypeResponse(ExpenseTypeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PaymentByBase(BaseModel):
    name: str
    description: Optional[str] = None


class PaymentByCreate(PaymentByBase):
    pass


class PaymentByUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PaymentByResponse(PaymentByBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PaymentMethodBase(BaseModel):
    name: str
    description: Optional[str] = None


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PaymentMethodResponse(PaymentMethodBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ExpenseBase(BaseModel):
    expense_type_id: Optional[int] = None
    payment_by_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    date: str
    items: str
    description: Optional[str] = None
    amount: float
    payment_status: str = "paid"


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    expense_type_id: Optional[int] = None
    payment_by_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    date: Optional[str] = None
    items: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    payment_status: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    expense_type_name: Optional[str] = None
    payment_by_name: Optional[str] = None
    payment_method_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
