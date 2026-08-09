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
        settings = SiteSettings(logo_url=None, site_name="WaveNotebook")
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
            "site_name": settings.site_name,
        },
    }


@router.put("", status_code=status.HTTP_200_OK)
async def update_settings(
    db: db_dependency,
    admin: admin_dependency,
    site_name: str = Form(None),
    logo: UploadFile = File(None),
):
    settings = get_or_create_settings(db)

    if site_name is not None:
        settings.site_name = site_name

    if logo:
        logo_url = await upload_file_to_storage(logo, 0)
        if logo_url:
            settings.logo_url = logo_url

    db.commit()
    db.refresh(settings)

    logger.info(f"✅ Settings Updated | Admin={admin.phone_number}")

    return {
        "message": "Settings updated successfully.",
        "settings": {
            "logo_url": settings.logo_url,
            "site_name": settings.site_name,
        },
    }