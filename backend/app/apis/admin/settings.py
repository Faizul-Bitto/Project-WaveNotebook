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


@router.put("", status_code=status.HTTP_200_OK)
async def update_settings(
    db: db_dependency,
    admin: admin_dependency,
    site_name: str = Form(None),
    page_title: str = Form(None),
    site_description: str = Form(None),
    contact_phone: str = Form(None),
    contact_email: str = Form(None),
    contact_address: str = Form(None),
    hotline_number: str = Form(None),
    facebook_url: str = Form(None),
    youtube_url: str = Form(None),
    instagram_url: str = Form(None),
    twitter_url: str = Form(None),
    whatsapp_number: str = Form(None),
    messenger_url: str = Form(None),
    privacy_policy: str = Form(None),
    terms_conditions: str = Form(None),
    refund_policy: str = Form(None),
    logo: UploadFile = File(None),
    favicon: UploadFile = File(None),
):
    settings = get_or_create_settings(db)

    if site_name is not None:
        settings.site_name = site_name
    if page_title is not None:
        settings.page_title = page_title
    if site_description is not None:
        settings.site_description = site_description
    if contact_phone is not None:
        settings.contact_phone = contact_phone
    if contact_email is not None:
        settings.contact_email = contact_email
    if contact_address is not None:
        settings.contact_address = contact_address
    if hotline_number is not None:
        settings.hotline_number = hotline_number
    if facebook_url is not None:
        settings.facebook_url = facebook_url
    if youtube_url is not None:
        settings.youtube_url = youtube_url
    if instagram_url is not None:
        settings.instagram_url = instagram_url
    if twitter_url is not None:
        settings.twitter_url = twitter_url
    if whatsapp_number is not None:
        settings.whatsapp_number = whatsapp_number
    if messenger_url is not None:
        settings.messenger_url = messenger_url
    if privacy_policy is not None:
        settings.privacy_policy = privacy_policy
    if terms_conditions is not None:
        settings.terms_conditions = terms_conditions
    if refund_policy is not None:
        settings.refund_policy = refund_policy

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
