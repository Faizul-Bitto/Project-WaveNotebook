from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import func, extract
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.expense import Expense
from app.models.expense_type import ExpenseType
from app.models.payment_by import PaymentBy
from app.models.payment_method import PaymentMethod
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseTypeCreate,
    ExpenseTypeUpdate,
    PaymentByCreate,
    PaymentByUpdate,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)

router = APIRouter(
    prefix="/admin/expenses",
    tags=["Admin - Expenses"],
)


def _parse_date(date_str: str):
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


    return True


# ==========================================================
# Expense Types
# ==========================================================

@router.post("/types", status_code=status.HTTP_201_CREATED)
async def create_expense_type(
    db: db_dependency, admin: admin_dependency, type_data: ExpenseTypeCreate
):
    try:
        existing = db.query(ExpenseType).filter(ExpenseType.name == type_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Expense type with this name already exists.",
            )

        new_type = ExpenseType(
            name=type_data.name,
            description=type_data.description,
            is_active=1,
        )
        db.add(new_type)
        db.commit()
        db.refresh(new_type)

        logger.info(f"✅ Expense Type Created | ID={new_type.id} | Name={new_type.name} | Admin={admin.phone_number}")

        return {
            "message": "Expense type created successfully.",
            "expense_type": {
                "id": new_type.id,
                "name": new_type.name,
                "description": new_type.description,
                "is_active": new_type.is_active,
                "created_at": new_type.created_at.isoformat() if new_type.created_at else None,
                "updated_at": new_type.updated_at.isoformat() if new_type.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Type Creation Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create expense type.")


@router.get("/types", status_code=status.HTTP_200_OK)
async def get_all_expense_types(
    db: db_dependency, admin: admin_dependency, skip: int = 0, limit: int = 100
):
    try:
        types = db.query(ExpenseType).offset(skip).limit(limit).all()
        total = db.query(ExpenseType).count()

        return {
            "message": "Expense types retrieved successfully.",
            "total": total,
            "expense_types": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "is_active": t.is_active,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in types
            ],
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving expense types | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expense types.")


@router.put("/types/{type_id}", status_code=status.HTTP_200_OK)
async def update_expense_type(
    db: db_dependency, admin: admin_dependency, type_id: int = Path(gt=0), type_data: ExpenseTypeUpdate = None
):
    try:
        expense_type = db.query(ExpenseType).filter(ExpenseType.id == type_id).first()
        if not expense_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense type not found.")

        if type_data.name is not None:
            existing = db.query(ExpenseType).filter(ExpenseType.name == type_data.name, ExpenseType.id != type_id).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Expense type with this name already exists.")
            expense_type.name = type_data.name
        if type_data.description is not None:
            expense_type.description = type_data.description
        if type_data.is_active is not None:
            expense_type.is_active = 1 if type_data.is_active else 0

        db.commit()
        db.refresh(expense_type)

        logger.info(f"✅ Expense Type Updated | ID={type_id} | Admin={admin.phone_number}")

        return {
            "message": "Expense type updated successfully.",
            "expense_type": {
                "id": expense_type.id,
                "name": expense_type.name,
                "description": expense_type.description,
                "is_active": expense_type.is_active,
                "created_at": expense_type.created_at.isoformat() if expense_type.created_at else None,
                "updated_at": expense_type.updated_at.isoformat() if expense_type.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Type Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update expense type.")


@router.delete("/types/{type_id}", status_code=status.HTTP_200_OK)
async def delete_expense_type(db: db_dependency, admin: admin_dependency, type_id: int = Path(gt=0)):
    try:
        expense_type = db.query(ExpenseType).filter(ExpenseType.id == type_id).first()
        if not expense_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense type not found.")

        type_name = expense_type.name
        db.delete(expense_type)
        db.commit()

        logger.info(f"✅ Expense Type Deleted | ID={type_id} | Name={type_name} | Admin={admin.phone_number}")

        return {"message": "Expense type deleted successfully.", "deleted_type_id": type_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Type Delete Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete expense type.")


# ==========================================================
# Payment By
# ==========================================================

@router.post("/payment-by", status_code=status.HTTP_201_CREATED)
async def create_payment_by(
    db: db_dependency, admin: admin_dependency, data: PaymentByCreate
):
    try:
        existing = db.query(PaymentBy).filter(PaymentBy.name == data.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment by with this name already exists.")

        new_payment_by = PaymentBy(name=data.name, description=data.description, is_active=1)
        db.add(new_payment_by)
        db.commit()
        db.refresh(new_payment_by)

        logger.info(f"✅ Payment By Created | ID={new_payment_by.id} | Name={new_payment_by.name} | Admin={admin.phone_number}")

        return {
            "message": "Payment by created successfully.",
            "payment_by": {
                "id": new_payment_by.id,
                "name": new_payment_by.name,
                "description": new_payment_by.description,
                "is_active": new_payment_by.is_active,
                "created_at": new_payment_by.created_at.isoformat() if new_payment_by.created_at else None,
                "updated_at": new_payment_by.updated_at.isoformat() if new_payment_by.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment By Creation Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create payment by.")


@router.get("/payment-by", status_code=status.HTTP_200_OK)
async def get_all_payment_by(db: db_dependency, admin: admin_dependency, skip: int = 0, limit: int = 100):
    try:
        items = db.query(PaymentBy).offset(skip).limit(limit).all()
        total = db.query(PaymentBy).count()

        return {
            "message": "Payment by list retrieved successfully.",
            "total": total,
            "items": [
                {
                    "id": i.id,
                    "name": i.name,
                    "description": i.description,
                    "is_active": i.is_active,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                }
                for i in items
            ],
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving payment by | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve payment by.")


@router.put("/payment-by/{by_id}", status_code=status.HTTP_200_OK)
async def update_payment_by(db: db_dependency, admin: admin_dependency, by_id: int = Path(gt=0), data: PaymentByUpdate = None):
    try:
        item = db.query(PaymentBy).filter(PaymentBy.id == by_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment by not found.")

        if data.name is not None:
            existing = db.query(PaymentBy).filter(PaymentBy.name == data.name, PaymentBy.id != by_id).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment by with this name already exists.")
            item.name = data.name
        if data.description is not None:
            item.description = data.description
        if data.is_active is not None:
            item.is_active = 1 if data.is_active else 0

        db.commit()
        db.refresh(item)

        logger.info(f"✅ Payment By Updated | ID={by_id} | Admin={admin.phone_number}")

        return {
            "message": "Payment by updated successfully.",
            "payment_by": {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment By Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update payment by.")


@router.delete("/payment-by/{by_id}", status_code=status.HTTP_200_OK)
async def delete_payment_by(db: db_dependency, admin: admin_dependency, by_id: int = Path(gt=0)):
    try:
        item = db.query(PaymentBy).filter(PaymentBy.id == by_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment by not found.")

        name = item.name
        db.delete(item)
        db.commit()

        logger.info(f"✅ Payment By Deleted | ID={by_id} | Name={name} | Admin={admin.phone_number}")

        return {"message": "Payment by deleted successfully.", "deleted_id": by_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment By Delete Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete payment by.")


# ==========================================================
# Payment Methods
# ==========================================================

@router.post("/payment-methods", status_code=status.HTTP_201_CREATED)
async def create_payment_method(db: db_dependency, admin: admin_dependency, data: PaymentMethodCreate):
    try:
        existing = db.query(PaymentMethod).filter(PaymentMethod.name == data.name).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment method with this name already exists.")

        new_method = PaymentMethod(name=data.name, description=data.description, is_active=1)
        db.add(new_method)
        db.commit()
        db.refresh(new_method)

        logger.info(f"✅ Payment Method Created | ID={new_method.id} | Name={new_method.name} | Admin={admin.phone_number}")

        return {
            "message": "Payment method created successfully.",
            "payment_method": {
                "id": new_method.id,
                "name": new_method.name,
                "description": new_method.description,
                "is_active": new_method.is_active,
                "created_at": new_method.created_at.isoformat() if new_method.created_at else None,
                "updated_at": new_method.updated_at.isoformat() if new_method.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment Method Creation Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create payment method.")


@router.get("/payment-methods", status_code=status.HTTP_200_OK)
async def get_all_payment_methods(db: db_dependency, admin: admin_dependency, skip: int = 0, limit: int = 100):
    try:
        items = db.query(PaymentMethod).offset(skip).limit(limit).all()
        total = db.query(PaymentMethod).count()

        return {
            "message": "Payment methods retrieved successfully.",
            "total": total,
            "items": [
                {
                    "id": i.id,
                    "name": i.name,
                    "description": i.description,
                    "is_active": i.is_active,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                }
                for i in items
            ],
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving payment methods | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve payment methods.")


@router.put("/payment-methods/{method_id}", status_code=status.HTTP_200_OK)
async def update_payment_method(db: db_dependency, admin: admin_dependency, method_id: int = Path(gt=0), data: PaymentMethodUpdate = None):
    try:
        item = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found.")

        if data.name is not None:
            existing = db.query(PaymentMethod).filter(PaymentMethod.name == data.name, PaymentMethod.id != method_id).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment method with this name already exists.")
            item.name = data.name
        if data.description is not None:
            item.description = data.description
        if data.is_active is not None:
            item.is_active = 1 if data.is_active else 0

        db.commit()
        db.refresh(item)

        logger.info(f"✅ Payment Method Updated | ID={method_id} | Admin={admin.phone_number}")

        return {
            "message": "Payment method updated successfully.",
            "payment_method": {
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment Method Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update payment method.")


@router.delete("/payment-methods/{method_id}", status_code=status.HTTP_200_OK)
async def delete_payment_method(db: db_dependency, admin: admin_dependency, method_id: int = Path(gt=0)):
    try:
        item = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found.")

        name = item.name
        db.delete(item)
        db.commit()

        logger.info(f"✅ Payment Method Deleted | ID={method_id} | Name={name} | Admin={admin.phone_number}")

        return {"message": "Payment method deleted successfully.", "deleted_id": method_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Payment Method Delete Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete payment method.")


# ==========================================================
# Dropdown data
# ==========================================================

@router.get("/summary", status_code=status.HTTP_200_OK)
async def get_expense_summary(
    db: db_dependency,
    admin: admin_dependency,
    period: str = Query("all", pattern="^(all|year|month|week|day)$"),
    year: int = Query(None),
    month: int = Query(None),
    date_filter: str = Query(None, alias="date"),
):
    try:
        query = db.query(Expense)

        if period == "year" and year:
            query = query.filter(extract("year", Expense.date) == year)
        elif period == "month" and year and month:
            query = query.filter(extract("year", Expense.date) == year, extract("month", Expense.date) == month)
        elif period == "week":
            from datetime import timedelta
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            query = query.filter(Expense.date >= week_start)
        elif period == "day" and date_filter:
            parsed = _parse_date(date_filter)
            if parsed is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )
            query = query.filter(Expense.date == parsed)

        # Total expense (all statuses)
        total_expense = query.with_entities(func.sum(Expense.amount)).scalar() or 0.0

        # Total paid
        total_paid = query.filter(Expense.payment_status == "paid").with_entities(func.sum(Expense.amount)).scalar() or 0.0

        # Total due
        total_due = query.filter(Expense.payment_status == "due").with_entities(func.sum(Expense.amount)).scalar() or 0.0

        return {
            "message": "Expense summary retrieved successfully.",
            "period": period,
            "year": year,
            "month": month,
            "total_expense": round(float(total_expense), 2),
            "total_paid": round(float(total_paid), 2),
            "total_due": round(float(total_due), 2),
            "net_expense": round(float(total_paid), 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving expense summary | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expense summary.")


@router.get("/dropdown", status_code=status.HTTP_200_OK)
async def get_expense_dropdowns(db: db_dependency, admin: admin_dependency):
    try:
        expense_types = db.query(ExpenseType).filter(ExpenseType.is_active == True).all()
        payment_by_list = db.query(PaymentBy).filter(PaymentBy.is_active == True).all()
        payment_methods = db.query(PaymentMethod).filter(PaymentMethod.is_active == True).all()

        return {
            "message": "Dropdown data retrieved successfully.",
            "expense_types": [{"id": t.id, "name": t.name} for t in expense_types],
            "payment_by": [{"id": p.id, "name": p.name} for p in payment_by_list],
            "payment_methods": [{"id": m.id, "name": m.name} for m in payment_methods],
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving dropdowns | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve dropdown data.")


# ==========================================================
# Expenses CRUD
# ==========================================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_expense(db: db_dependency, admin: admin_dependency, expense_data: ExpenseCreate):
    try:
        parsed_date = _parse_date(expense_data.date)
        if parsed_date is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

        expense = Expense(
            expense_type_id=expense_data.expense_type_id,
            payment_by_id=expense_data.payment_by_id,
            payment_method_id=expense_data.payment_method_id,
            date=parsed_date,
            items=expense_data.items,
            description=expense_data.description,
            amount=expense_data.amount,
            payment_status=expense_data.payment_status,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)

        logger.info(f"✅ Expense Created | ID={expense.id} | Amount={expense.amount} | Admin={admin.phone_number}")

        return {
            "message": "Expense created successfully.",
            "expense": _serialize_expense(db, expense),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Creation Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create expense.")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_expenses(
    db: db_dependency,
    admin: admin_dependency,
    status_filter: str = Query(None, alias="status"),
    type_filter: int = Query(None, alias="type_id"),
    period: str = Query("all", pattern="^(all|year|month|day)$"),
    year: int = Query(None),
    month: int = Query(None),
    date_filter: str = Query(None, alias="date"),
    skip: int = 0,
    limit: int = 100,
):
    try:
        query = db.query(Expense)

        if status_filter:
            query = query.filter(Expense.payment_status == status_filter)
        if type_filter:
            query = query.filter(Expense.expense_type_id == type_filter)

        if period == "year" and year:
            query = query.filter(extract("year", Expense.date) == year)
        elif period == "month" and year and month:
            query = query.filter(
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
        elif period == "day" and date_filter:
            parsed = _parse_date(date_filter)
            if parsed is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )
            query = query.filter(Expense.date == parsed)

        total = query.order_by(None).count()
        expenses = query.order_by(Expense.date.desc()).offset(skip).limit(limit).all()

        return {
            "message": "Expenses retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "expenses": [_serialize_expense(db, e) for e in expenses],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving expenses | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expenses.")


@router.get("/{expense_id}", status_code=status.HTTP_200_OK)
async def get_expense_by_id(db: db_dependency, admin: admin_dependency, expense_id: int = Path(gt=0)):
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

        return {
            "message": "Expense retrieved successfully.",
            "expense": _serialize_expense(db, expense),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving expense | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve expense.")


@router.put("/{expense_id}", status_code=status.HTTP_200_OK)
async def update_expense(db: db_dependency, admin: admin_dependency, expense_id: int = Path(gt=0), expense_data: ExpenseUpdate = None):
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

        if expense_data.expense_type_id is not None:
            expense.expense_type_id = expense_data.expense_type_id
        if expense_data.payment_by_id is not None:
            expense.payment_by_id = expense_data.payment_by_id
        if expense_data.payment_method_id is not None:
            expense.payment_method_id = expense_data.payment_method_id
        if expense_data.date is not None:
            parsed_date = _parse_date(expense_data.date)
            if parsed_date is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")
            expense.date = parsed_date
        if expense_data.items is not None:
            expense.items = expense_data.items
        if expense_data.description is not None:
            expense.description = expense_data.description
        if expense_data.amount is not None:
            expense.amount = expense_data.amount
        if expense_data.payment_status is not None:
            expense.payment_status = expense_data.payment_status

        db.commit()
        db.refresh(expense)

        logger.info(f"✅ Expense Updated | ID={expense_id} | Admin={admin.phone_number}")

        return {
            "message": "Expense updated successfully.",
            "expense": _serialize_expense(db, expense),
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update expense.")


@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
async def delete_expense(db: db_dependency, admin: admin_dependency, expense_id: int = Path(gt=0)):
    try:
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

        db.delete(expense)
        db.commit()

        logger.info(f"✅ Expense Deleted | ID={expense_id} | Admin={admin.phone_number}")

        return {"message": "Expense deleted successfully.", "deleted_id": expense_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Expense Delete Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete expense.")


# ==========================================================
# Helper
# ==========================================================

def _serialize_expense(db, expense):
    """Serialize an Expense model to dict with related names."""
    type_name = None
    by_name = None
    method_name = None

    if expense.expense_type_id:
        t = db.query(ExpenseType).filter(ExpenseType.id == expense.expense_type_id).first()
        type_name = t.name if t else None
    if expense.payment_by_id:
        p = db.query(PaymentBy).filter(PaymentBy.id == expense.payment_by_id).first()
        by_name = p.name if p else None
    if expense.payment_method_id:
        m = db.query(PaymentMethod).filter(PaymentMethod.id == expense.payment_method_id).first()
        method_name = m.name if m else None

    return {
        "id": expense.id,
        "expense_type_id": expense.expense_type_id,
        "expense_type_name": type_name,
        "payment_by_id": expense.payment_by_id,
        "payment_by_name": by_name,
        "payment_method_id": expense.payment_method_id,
        "payment_method_name": method_name,
        "date": expense.date.isoformat() if expense.date else None,
        "items": expense.items,
        "description": expense.description,
        "amount": str(expense.amount),
        "payment_status": expense.payment_status,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
        "updated_at": expense.updated_at.isoformat() if expense.updated_at else None,
    }
