from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.site_settings import SiteSettings
from app.utils.file_upload import upload_file_to_storage

router = APIRouter(
    prefix="/admin/settings",
    tags=["Admin - Settings"],
)


def get_or_create_settings(db):
    settings = db.query(SiteSettings).first()
    if not settings:
        settings = SiteSettings(logo_url=None, favicon_url=None, site_name="WaveNotebook", page_title=None)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", status_code=status.HTTP_200_OK)
async def get_settings(db: db_dependency, admin: admin_dependency):
    settings = get_or_create_settings(db)
    return {
        "message": "Settings retrieved successfully.",
        "settings": {
            "logo_url": settings.logo_url,
            "favicon_url": settings.favicon_url,
            "site_name": settings.site_name,
            "page_title": settings.page_title,
            "site_description": settings.site_description,
            "contact_phone": settings.contact_phone,
            "contact_email": settings.contact_email,
            "contact_address": settings.contact_address,
            "hotline_number": settings.hotline_number,
            "website_url": settings.website_url,
            "facebook_url": settings.facebook_url,
            "youtube_url": settings.youtube_url,
            "instagram_url": settings.instagram_url,
            "twitter_url": settings.twitter_url,
            "whatsapp_number": settings.whatsapp_number,
            "messenger_url": settings.messenger_url,
            "order_whatsapp_number": settings.order_whatsapp_number,
            "order_call_number": settings.order_call_number,
            "privacy_policy": settings.privacy_policy,
            "terms_conditions": settings.terms_conditions,
            "refund_policy": settings.refund_policy,
        },
    }


@router.put("", status_code=status.HTTP_200_OK)
async def update_settings(
    db: db_dependency,
    admin: admin_dependency,
    site_name: str = Form(""),
    page_title: str = Form(""),
    site_description: str = Form(""),
    contact_phone: str = Form(""),
    contact_email: str = Form(""),
    contact_address: str = Form(""),
    hotline_number: str = Form(""),
    website_url: str = Form(""),
    facebook_url: str = Form(""),
    youtube_url: str = Form(""),
    instagram_url: str = Form(""),
    twitter_url: str = Form(""),
    whatsapp_number: str = Form(""),
    messenger_url: str = Form(""),
    order_whatsapp_number: str = Form(""),
    order_call_number: str = Form(""),
    privacy_policy: str = Form(""),
    terms_conditions: str = Form(""),
    refund_policy: str = Form(""),
    logo: UploadFile = File(None),
    favicon: UploadFile = File(None),
):
    settings = get_or_create_settings(db)

    # All text fields default to "" so cleared fields are always saved
    # (even when the browser omits the field from multipart form data).
    # Empty strings are saved as-is so the frontend form can distinguish
    # "cleared by user" from "never set" when using nullish coalescing.
    _fields = [
        "site_name", "page_title", "site_description",
        "contact_phone", "contact_email", "contact_address",
        "hotline_number", "website_url",
        "facebook_url", "youtube_url", "instagram_url", "twitter_url",
        "whatsapp_number", "messenger_url",
        "order_whatsapp_number", "order_call_number",
        "privacy_policy", "terms_conditions", "refund_policy",
    ]
    for _field in _fields:
        _val = locals()[_field]
        setattr(settings, _field, _val)

    if logo:
        logo_url = await upload_file_to_storage(logo, "logo")
        if logo_url:
            settings.logo_url = logo_url

    if favicon:
        favicon_url = await upload_file_to_storage(favicon, "favicon")
        if favicon_url:
            settings.favicon_url = favicon_url

    db.commit()
    db.refresh(settings)

    logger.info(f"✅ Settings Updated | Admin={admin.phone_number}")

    return {
        "message": "Settings updated successfully.",
        "settings": {
            "logo_url": settings.logo_url,
            "favicon_url": settings.favicon_url,
            "site_name": settings.site_name,
            "page_title": settings.page_title,
            "site_description": settings.site_description,
            "contact_phone": settings.contact_phone,
            "contact_email": settings.contact_email,
            "contact_address": settings.contact_address,
            "hotline_number": settings.hotline_number,
            "website_url": settings.website_url,
            "facebook_url": settings.facebook_url,
            "youtube_url": settings.youtube_url,
            "instagram_url": settings.instagram_url,
            "twitter_url": settings.twitter_url,
            "whatsapp_number": settings.whatsapp_number,
            "messenger_url": settings.messenger_url,
            "order_whatsapp_number": settings.order_whatsapp_number,
            "order_call_number": settings.order_call_number,
            "privacy_policy": settings.privacy_policy,
            "terms_conditions": settings.terms_conditions,
            "refund_policy": settings.refund_policy,
        },
    }
