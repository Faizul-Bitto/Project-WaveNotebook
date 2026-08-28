from fastapi import APIRouter, Response
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.banner import Banner

router = APIRouter(
    prefix="/banners",
    tags=["Banners"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_banners(db: db_dependency, response: Response):
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

        # Never let browsers cache this JSON — stale banner lists are what
        # cause the "old banner flashes first on refresh" behaviour.
        response.headers["Cache-Control"] = "no-store"

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
                    # Used by the frontend as a cache-buster on the image URL
                    # so a replaced banner image is fetched fresh, instantly.
                    "updated_at": banner.updated_at.isoformat() if banner.updated_at else None,
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