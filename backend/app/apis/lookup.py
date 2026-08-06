from fastapi import APIRouter
from starlette import status

from app.constants.districts import BANGLADESH_DISTRICTS
from app.constants.order_status import ORDER_STATUSES

router = APIRouter(
    prefix="/lookup",
    tags=["Lookup"],
)


@router.get("/districts", status_code=status.HTTP_200_OK)
async def get_districts():
    """
    Get all Bangladesh districts for dropdown.
    GET /lookup/districts
    """
    return {
        "message": "Districts retrieved successfully.",
        "districts": BANGLADESH_DISTRICTS,
    }


@router.get("/order-statuses", status_code=status.HTTP_200_OK)
async def get_order_statuses():
    """
    Get all order statuses for dropdown.
    GET /lookup/order-statuses
    """
    return {
        "message": "Order statuses retrieved successfully.",
        "statuses": ORDER_STATUSES,
    }