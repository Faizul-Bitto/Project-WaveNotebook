import re
from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.schemas.attribute import (
    AttributeCreate,
    AttributeUpdate,
    AttributeOptionCreate,
    AttributeOptionUpdate,
)

router = APIRouter(
    prefix="/admin/attributes",
    tags=["Admin - Attributes"],
)


def generate_slug(name: str) -> str:
    """
    Generate slug from attribute name.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_attribute(
    db: db_dependency, admin: admin_dependency, attribute_data: AttributeCreate
):
    """
    Create a new attribute (admin only).
    POST /admin/attributes
    """

    try:
        slug = generate_slug(attribute_data.name)

        existing_attribute = db.query(Attribute).filter(Attribute.slug == slug).first()

        if existing_attribute:
            logger.warning(
                f"⚠️ Attribute Creation Failed | "
                f"Slug={slug} already exists | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Attribute with this name already exists.",
            )

        new_attribute = Attribute(name=attribute_data.name, slug=slug, is_active=True)

        db.add(new_attribute)
        db.commit()
        db.refresh(new_attribute)

        logger.info(
            f"✅ Attribute Created | "
            f"ID={new_attribute.id} | "
            f"Name={new_attribute.name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute created successfully.",
            "attribute": {
                "id": new_attribute.id,
                "name": new_attribute.name,
                "slug": new_attribute.slug,
                "is_active": new_attribute.is_active,
                "created_at": new_attribute.created_at.isoformat(),
                "updated_at": new_attribute.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Creation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attribute.",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_attributes(
    db: db_dependency,
    admin: admin_dependency,
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
):
    """
    Get all attributes (active + inactive) for admin.
    GET /admin/attributes
    """

    try:
        query = db.query(Attribute)

        if is_active is not None:
            query = query.filter(Attribute.is_active == is_active)

        attributes = query.offset(skip).limit(limit).all()
        total = db.query(Attribute).count()

        logger.info(
            f"📋 Attributes Retrieved | "
            f"Count={len(attributes)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attributes retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "attributes": [
                {
                    "id": attr.id,
                    "name": attr.name,
                    "slug": attr.slug,
                    "is_active": attr.is_active,
                    "created_at": attr.created_at.isoformat(),
                    "updated_at": attr.updated_at.isoformat(),
                }
                for attr in attributes
            ],
        }

    except Exception as e:
        logger.error(
            f"❌ Error retrieving attributes | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attributes.",
        )


@router.get("/{attribute_id}", status_code=status.HTTP_200_OK)
async def get_attribute_by_id(
    db: db_dependency, admin: admin_dependency, attribute_id: int = Path(gt=0)
):
    """
    Get single attribute details with options.
    GET /admin/attributes/{id}
    """

    try:
        attribute = db.query(Attribute).filter(Attribute.id == attribute_id).first()

        if not attribute:
            logger.warning(
                f"⚠️ Attribute Not Found | "
                f"ID={attribute_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        options = (
            db.query(AttributeOption)
            .filter(AttributeOption.attribute_id == attribute_id)
            .all()
        )

        logger.info(
            f"📋 Attribute Retrieved | "
            f"ID={attribute.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute retrieved successfully.",
            "attribute": {
                "id": attribute.id,
                "name": attribute.name,
                "slug": attribute.slug,
                "is_active": attribute.is_active,
                "options": [
                    {
                        "id": opt.id,
                        "value": opt.value,
                        "additional_price": str(opt.additional_price),
                        "created_at": opt.created_at.isoformat(),
                    }
                    for opt in options
                ],
                "created_at": attribute.created_at.isoformat(),
                "updated_at": attribute.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving attribute | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute.",
        )


@router.put("/{attribute_id}", status_code=status.HTTP_200_OK)
async def update_attribute(
    db: db_dependency,
    admin: admin_dependency,
    attribute_id: int = Path(gt=0),
    attribute_data: AttributeUpdate = None,
):
    """
    Update attribute details.
    PUT /admin/attributes/{id}
    """

    try:
        attribute = db.query(Attribute).filter(Attribute.id == attribute_id).first()

        if not attribute:
            logger.warning(
                f"⚠️ Attribute Not Found | "
                f"ID={attribute_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        if attribute_data.name and attribute_data.name != attribute.name:
            new_slug = generate_slug(attribute_data.name)
            existing = db.query(Attribute).filter(Attribute.slug == new_slug).first()

            if existing:
                logger.warning(
                    f"⚠️ Attribute Update Failed | "
                    f"Slug={new_slug} already exists | "
                    f"Admin={admin.phone_number}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Attribute with this name already exists.",
                )

            attribute.slug = new_slug

        update_data = attribute_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != "name":  # name handled above
                setattr(attribute, field, value)
            else:
                setattr(attribute, field, value)

        db.commit()
        db.refresh(attribute)

        logger.info(
            f"✅ Attribute Updated | "
            f"ID={attribute.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute updated successfully.",
            "attribute": {
                "id": attribute.id,
                "name": attribute.name,
                "slug": attribute.slug,
                "is_active": attribute.is_active,
                "created_at": attribute.created_at.isoformat(),
                "updated_at": attribute.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attribute.",
        )


@router.delete("/{attribute_id}", status_code=status.HTTP_200_OK)
async def delete_attribute(
    db: db_dependency, admin: admin_dependency, attribute_id: int = Path(gt=0)
):
    """
    Delete attribute and cascade delete options.
    DELETE /admin/attributes/{id}
    """

    try:
        attribute = db.query(Attribute).filter(Attribute.id == attribute_id).first()

        if not attribute:
            logger.warning(
                f"⚠️ Attribute Delete Failed | "
                f"ID={attribute_id} not found | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        attribute_name = attribute.name

        db.delete(attribute)
        db.commit()

        logger.info(
            f"✅ Attribute Deleted | "
            f"ID={attribute_id} | "
            f"Name={attribute_name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute deleted successfully.",
            "deleted_attribute_id": attribute_id,
            "deleted_attribute_name": attribute_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attribute.",
        )
