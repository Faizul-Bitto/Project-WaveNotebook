from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.schemas.attribute_option import (
    AttributeOptionCreate,
    AttributeOptionUpdate,
)

router = APIRouter(
    prefix="/admin/attribute-options",
    tags=["Admin - Attribute Options"],
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_attribute_option(
    db: db_dependency, admin: admin_dependency, option_data: AttributeOptionCreate
):
    """
    Create a new attribute option (admin only).
    POST /admin/attribute-options
    """

    try:
        # Check if attribute exists
        attribute = (
            db.query(Attribute).filter(Attribute.id == option_data.attribute_id).first()
        )

        if not attribute:
            logger.warning(
                f"⚠️ Attribute Not Found | "
                f"ID={option_data.attribute_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        new_option = AttributeOption(
            attribute_id=option_data.attribute_id,
            value=option_data.value,
                    )

        db.add(new_option)
        db.commit()
        db.refresh(new_option)

        logger.info(
            f"✅ Attribute Option Created | "
            f"ID={new_option.id} | "
            f"Attribute ID={option_data.attribute_id} | "
            f"Value={option_data.value} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute option created successfully.",
            "option": {
                "id": new_option.id,
                "attribute_id": new_option.attribute_id,
                "value": new_option.value,
                                "created_at": new_option.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Option Creation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attribute option.",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_attribute_options(
    db: db_dependency,
    admin: admin_dependency,
    attribute_id: int = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all attribute options (optional filter by attribute_id).
    GET /admin/attribute-options
    """

    try:
        query = db.query(AttributeOption)

        if attribute_id:
            query = query.filter(AttributeOption.attribute_id == attribute_id)

        options = query.offset(skip).limit(limit).all()
        total = db.query(AttributeOption).count()

        logger.info(
            f"📋 Attribute Options Retrieved | "
            f"Count={len(options)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute options retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "options": [
                {
                    "id": opt.id,
                    "attribute_id": opt.attribute_id,
                    "value": opt.value,
                                        "created_at": opt.created_at.isoformat(),
                }
                for opt in options
            ],
        }

    except Exception as e:
        logger.error(
            f"❌ Error retrieving attribute options | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute options.",
        )


@router.get("/{option_id}", status_code=status.HTTP_200_OK)
async def get_attribute_option_by_id(
    db: db_dependency, admin: admin_dependency, option_id: int = Path(gt=0)
):
    """
    Get single attribute option details.
    GET /admin/attribute-options/{id}
    """

    try:
        option = (
            db.query(AttributeOption).filter(AttributeOption.id == option_id).first()
        )

        if not option:
            logger.warning(
                f"⚠️ Attribute Option Not Found | "
                f"ID={option_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute option not found.",
            )

        logger.info(
            f"📋 Attribute Option Retrieved | "
            f"ID={option.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute option retrieved successfully.",
            "option": {
                "id": option.id,
                "attribute_id": option.attribute_id,
                "value": option.value,
                                "created_at": option.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving attribute option | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute option.",
        )


@router.put("/{option_id}", status_code=status.HTTP_200_OK)
async def update_attribute_option(
    db: db_dependency,
    admin: admin_dependency,
    option_id: int = Path(gt=0),
    option_data: AttributeOptionUpdate = None,
):
    """
    Update attribute option.
    PUT /admin/attribute-options/{id}
    """

    try:
        option = (
            db.query(AttributeOption).filter(AttributeOption.id == option_id).first()
        )

        if not option:
            logger.warning(
                f"⚠️ Attribute Option Not Found | "
                f"ID={option_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute option not found.",
            )

        update_data = option_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(option, field, value)

        db.commit()
        db.refresh(option)

        logger.info(
            f"✅ Attribute Option Updated | "
            f"ID={option.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute option updated successfully.",
            "option": {
                "id": option.id,
                "attribute_id": option.attribute_id,
                "value": option.value,
                                "created_at": option.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Option Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attribute option.",
        )


@router.delete("/{option_id}", status_code=status.HTTP_200_OK)
async def delete_attribute_option(
    db: db_dependency, admin: admin_dependency, option_id: int = Path(gt=0)
):
    """
    Delete attribute option.
    DELETE /admin/attribute-options/{id}
    """

    try:
        option = (
            db.query(AttributeOption).filter(AttributeOption.id == option_id).first()
        )

        if not option:
            logger.warning(
                f"⚠️ Attribute Option Not Found | "
                f"ID={option_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute option not found.",
            )

        option_value = option.value
        attribute_id = option.attribute_id

        db.delete(option)
        db.commit()

        logger.info(
            f"✅ Attribute Option Deleted | "
            f"ID={option_id} | "
            f"Attribute ID={attribute_id} | "
            f"Value={option_value} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Attribute option deleted successfully.",
            "deleted_option_id": option_id,
            "deleted_option_value": option_value,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Attribute Option Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete attribute option.",
        )
