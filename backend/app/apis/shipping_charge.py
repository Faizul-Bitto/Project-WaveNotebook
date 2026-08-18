from fastapi import APIRouter, HTTPException
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.shipping_charge import ShippingCharge

router = APIRouter(
    prefix="/shipping-charges",
    tags=["Shipping Charges"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def list_shipping_charges(db: db_dependency):
    try:
        charges = db.query(ShippingCharge).filter(ShippingCharge.is_active == True).order_by(ShippingCharge.id).all()
        result = [
            {
                "id": c.id,
                "zone_name": c.zone_name,
                "amount": c.amount,
            }
            for c in charges
        ]
        return {
            "message": "Shipping charges retrieved successfully.",
            "shipping_charges": result,
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving shipping charges | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping charges.",
        )
