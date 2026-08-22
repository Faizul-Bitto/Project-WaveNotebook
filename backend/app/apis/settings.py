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
    Get public site settings (logo, site name, footer content, social links, policies).
    GET /settings
    """
    settings = db.query(SiteSettings).first()

    if not settings:
        return {
            "message": "Settings retrieved successfully.",
            "settings": {
                "logo_url": None,
                "favicon_url": None,
                "site_name": "WaveNotebook",
                "page_title": None,
                "site_description": None,
                "contact_phone": None,
                "contact_email": None,
                "contact_address": None,
                "hotline_number": None,
                "facebook_url": None,
                "youtube_url": None,
                "instagram_url": None,
                "twitter_url": None,
                "whatsapp_number": None,
                "messenger_url": None,
                "privacy_policy": None,
                "terms_conditions": None,
                "refund_policy": None,
            },
        }

    return {
        "message": "Settings retrieved successfully.",
            "settings": {
                "logo_url": settings.logo_url,
                "favicon_url": settings.favicon_url,
                "site_name": settings.site_name or "WaveNotebook",
                "page_title": settings.page_title,
                "site_description": settings.site_description,
                "contact_phone": settings.contact_phone,
                "contact_email": settings.contact_email,
                "contact_address": settings.contact_address,
                "hotline_number": settings.hotline_number,
                "facebook_url": settings.facebook_url,
                "youtube_url": settings.youtube_url,
                "instagram_url": settings.instagram_url,
                "twitter_url": settings.twitter_url,
                "whatsapp_number": settings.whatsapp_number,
                "messenger_url": settings.messenger_url,
                "privacy_policy": settings.privacy_policy,
                "terms_conditions": settings.terms_conditions,
                "refund_policy": settings.refund_policy,
            },
    }
