from fastapi import APIRouter
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.banner import Banner

router = APIRouter(
    prefix="/banners",
    tags=["Banners"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_banners(db: db_dependency):
    """
    Get all active banners for frontend.
    GET /banners
    """
    try:
        banners = (
            db.query(Banner)
            .filter(Banner.is_active == 1)
            .order_by(Banner.sort_order.asc())
            .all()
        )

        return {
            "message": "Banners retrieved successfully.",
            "banners": [
                {
                    "id": banner.id,
                    "title": banner.title,
                    "subtitle": banner.subtitle,
                    "image_url": banner.image_url,
                    "link_url": banner.link_url,
                    "sort_order": banner.sort_order,
                }
                for banner in banners
            ],
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving banners | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve banners.",
        )