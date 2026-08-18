from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.shipping_charge import ShippingCharge
from app.schemas.shipping_charge import ShippingChargeCreate, ShippingChargeUpdate

router = APIRouter(
    prefix="/admin/shipping-charges",
    tags=["Admin - Shipping Charges"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def list_shipping_charges(db: db_dependency, admin: admin_dependency):
    try:
        charges = db.query(ShippingCharge).order_by(ShippingCharge.id).all()
        result = [
            {
                "id": c.id,
                "zone_name": c.zone_name,
                "amount": c.amount,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in charges
        ]
        return {
            "message": "Shipping charges retrieved successfully.",
            "shipping_charges": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing shipping charges | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping charges.",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_shipping_charge(
    db: db_dependency,
    admin: admin_dependency,
    payload: ShippingChargeCreate,
):
    try:
        existing = db.query(ShippingCharge).filter(ShippingCharge.zone_name == payload.zone_name.strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A shipping charge for this zone already exists.",
            )

        charge = ShippingCharge(
            zone_name=payload.zone_name.strip(),
            amount=payload.amount,
            is_active=payload.is_active,
        )
        db.add(charge)
        db.commit()
        db.refresh(charge)

        logger.info(f"✅ Shipping Charge Created | Zone={charge.zone_name} | Amount={charge.amount} | Admin={admin.phone_number}")

        return {
            "message": "Shipping charge created successfully.",
            "shipping_charge": {
                "id": charge.id,
                "zone_name": charge.zone_name,
                "amount": charge.amount,
                "is_active": charge.is_active,
                "created_at": charge.created_at.isoformat(),
                "updated_at": charge.updated_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating shipping charge | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shipping charge.",
        )


@router.put("/{charge_id}", status_code=status.HTTP_200_OK)
async def update_shipping_charge(
    db: db_dependency,
    admin: admin_dependency,
    charge_id: int = Path(gt=0),
    payload: ShippingChargeUpdate = None,
):
    try:
        charge = db.query(ShippingCharge).filter(ShippingCharge.id == charge_id).first()
        if not charge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping charge not found.",
            )

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided.",
            )

        if payload.zone_name is not None:
            zone_name = payload.zone_name.strip()
            if not zone_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Zone name cannot be empty.",
                )
            existing = db.query(ShippingCharge).filter(
                ShippingCharge.zone_name == zone_name,
                ShippingCharge.id != charge_id,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Another shipping charge with this zone name already exists.",
                )
            charge.zone_name = zone_name

        if payload.amount is not None:
            charge.amount = payload.amount

        if payload.is_active is not None:
            charge.is_active = payload.is_active

        db.commit()
        db.refresh(charge)

        logger.info(f"✅ Shipping Charge Updated | ID={charge_id} | Zone={charge.zone_name} | Amount={charge.amount} | Admin={admin.phone_number}")

        return {
            "message": "Shipping charge updated successfully.",
            "shipping_charge": {
                "id": charge.id,
                "zone_name": charge.zone_name,
                "amount": charge.amount,
                "is_active": charge.is_active,
                "created_at": charge.created_at.isoformat(),
                "updated_at": charge.updated_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error updating shipping charge | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shipping charge.",
        )


@router.delete("/{charge_id}", status_code=status.HTTP_200_OK)
async def delete_shipping_charge(
    db: db_dependency,
    admin: admin_dependency,
    charge_id: int = Path(gt=0),
):
    try:
        charge = db.query(ShippingCharge).filter(ShippingCharge.id == charge_id).first()
        if not charge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping charge not found.",
            )

        db.delete(charge)
        db.commit()

        logger.info(f"✅ Shipping Charge Deleted | ID={charge_id} | Admin={admin.phone_number}")

        return {
            "message": "Shipping charge deleted successfully.",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error deleting shipping charge | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete shipping charge.",
        )
