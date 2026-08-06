from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.banner import Banner
from app.utils.file_upload import upload_file_to_storage

router = APIRouter(
    prefix="/admin/banners",
    tags=["Admin - Banners"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_banners(db: db_dependency, admin: admin_dependency):
    """
    Get all banners (admin).
    GET /admin/banners
    """
    try:
        banners = db.query(Banner).order_by(Banner.sort_order.asc()).all()

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
                    "is_active": banner.is_active,
                    "created_at": banner.created_at.isoformat(),
                    "updated_at": banner.updated_at.isoformat(),
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_banner(
    db: db_dependency,
    admin: admin_dependency,
    title: str = Form(...),
    subtitle: str = Form(None),
    link_url: str = Form(None),
    sort_order: int = Form(0),
    is_active: bool = Form(True),
    image: UploadFile = File(...),
):
    """
    Create banner with image upload.
    POST /admin/banners
    """
    try:
        # Upload image
        image_url = upload_file_to_storage(image, "banner")
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to upload banner image.",
            )

        # Create banner
        new_banner = Banner(
            title=title,
            subtitle=subtitle,
            image_url=image_url,
            link_url=link_url,
            sort_order=sort_order,
            is_active=1 if is_active else 0,
        )

        db.add(new_banner)
        db.commit()
        db.refresh(new_banner)

        logger.info(
            f"✅ Banner Created | ID={new_banner.id} | Title={title} | Admin={admin.phone_number}"
        )

        return {
            "message": "Banner created successfully.",
            "banner": {
                "id": new_banner.id,
                "title": new_banner.title,
                "subtitle": new_banner.subtitle,
                "image_url": new_banner.image_url,
                "link_url": new_banner.link_url,
                "sort_order": new_banner.sort_order,
                "is_active": new_banner.is_active,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Banner Creation Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create banner.",
        )


@router.put("/{banner_id}", status_code=status.HTTP_200_OK)
async def update_banner(
    db: db_dependency,
    admin: admin_dependency,
    banner_id: int,
    title: str = Form(None),
    subtitle: str = Form(None),
    link_url: str = Form(None),
    sort_order: int = Form(None),
    is_active: bool = Form(None),
    image: UploadFile = File(None),
):
    """
    Update banner.
    PUT /admin/banners/{banner_id}
    """
    try:
        banner = db.query(Banner).filter(Banner.id == banner_id).first()

        if not banner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found.",
            )

        # Update fields
        if title is not None:
            banner.title = title
        if subtitle is not None:
            banner.subtitle = subtitle
        if link_url is not None:
            banner.link_url = link_url
        if sort_order is not None:
            banner.sort_order = sort_order
        if is_active is not None:
            banner.is_active = 1 if is_active else 0

        # Upload new image if provided
        if image:
            image_url = upload_file_to_storage(image, "banner")
            if image_url:
                banner.image_url = image_url

        db.commit()
        db.refresh(banner)

        logger.info(
            f"✅ Banner Updated | ID={banner.id} | Title={banner.title} | Admin={admin.phone_number}"
        )

        return {
            "message": "Banner updated successfully.",
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "subtitle": banner.subtitle,
                "image_url": banner.image_url,
                "link_url": banner.link_url,
                "sort_order": banner.sort_order,
                "is_active": banner.is_active,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Banner Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update banner.",
        )


@router.delete("/{banner_id}", status_code=status.HTTP_200_OK)
async def delete_banner(
    db: db_dependency, admin: admin_dependency, banner_id: int
):
    """
    Delete banner.
    DELETE /admin/banners/{banner_id}
    """
    try:
        banner = db.query(Banner).filter(Banner.id == banner_id).first()

        if not banner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Banner not found.",
            )

        db.delete(banner)
        db.commit()

        logger.info(
            f"✅ Banner Deleted | ID={banner_id} | Title={banner.title} | Admin={admin.phone_number}"
        )

        return {
            "message": "Banner deleted successfully.",
            "deleted_banner_id": banner_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Banner Delete Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete banner.",
        )