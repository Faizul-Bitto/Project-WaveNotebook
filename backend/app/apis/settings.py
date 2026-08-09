from fastapi import APIRouter
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.site_settings import SiteSettings

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_site_settings(db: db_dependency):
    """
    Get public site settings (logo, site name).
    GET /settings
    """
    settings = db.query(SiteSettings).first()

    if not settings:
        return {
            "message": "Settings retrieved successfully.",
            "settings": {
                "logo_url": None,
                "site_name": "WaveNotebook",
            },
        }

    return {
        "message": "Settings retrieved successfully.",
        "settings": {
            "logo_url": settings.logo_url,
            "site_name": settings.site_name or "WaveNotebook",
        },
    }