from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption

router = APIRouter(
    prefix="/attribute-options",
    tags=["Attribute Options"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_attribute_options(
    db: db_dependency, attribute_id: int = None, skip: int = 0, limit: int = 100
):
    """
    Retrieve all active attribute options (optional filter by attribute_id).
    GET /attribute-options
    """

    try:
        query = (
            db.query(AttributeOption)
            .join(Attribute, AttributeOption.attribute_id == Attribute.id)
            .filter(Attribute.is_active == True)
        )

        if attribute_id:
            query = query.filter(AttributeOption.attribute_id == attribute_id)

        options = query.offset(skip).limit(limit).all()
        total = (
            db.query(AttributeOption)
            .join(Attribute, AttributeOption.attribute_id == Attribute.id)
            .filter(Attribute.is_active == True)
            .count()
        )

        logger.info(f"📋 Attribute Options Retrieved | " f"Count={len(options)}")

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
                    "additional_price": str(opt.additional_price),
                }
                for opt in options
            ],
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving attribute options | " f"Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute options.",
        )


@router.get("/{option_id}", status_code=status.HTTP_200_OK)
async def get_attribute_option_by_id(db: db_dependency, option_id: int = Path(gt=0)):
    """
    Retrieve a single attribute option by ID.
    GET /attribute-options/{id}
    """

    try:
        option = (
            db.query(AttributeOption)
            .join(Attribute, AttributeOption.attribute_id == Attribute.id)
            .filter(AttributeOption.id == option_id, Attribute.is_active == True)
            .first()
        )

        if not option:
            logger.warning(f"⚠️ Attribute Option Not Found | " f"ID={option_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute option not found.",
            )

        logger.info(f"📋 Attribute Option Retrieved | " f"ID={option.id}")

        return {
            "message": "Attribute option retrieved successfully.",
            "option": {
                "id": option.id,
                "attribute_id": option.attribute_id,
                "value": option.value,
                "additional_price": str(option.additional_price),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving attribute option | " f"Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute option.",
        )


@router.get("/by-attribute/{attribute_id}", status_code=status.HTTP_200_OK)
async def get_options_by_attribute(db: db_dependency, attribute_id: int = Path(gt=0)):
    """
    Get all options for a specific attribute.
    GET /attribute-options/by-attribute/{attribute_id}
    """

    try:
        attribute = (
            db.query(Attribute)
            .filter(Attribute.id == attribute_id, Attribute.is_active == True)
            .first()
        )

        if not attribute:
            logger.warning(f"⚠️ Attribute Not Found | " f"ID={attribute_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        options = (
            db.query(AttributeOption)
            .filter(AttributeOption.attribute_id == attribute_id)
            .all()
        )

        logger.info(
            f"📋 Attribute Options Retrieved | "
            f"Attribute ID={attribute_id} | "
            f"Count={len(options)}"
        )

        return {
            "message": "Attribute options retrieved successfully.",
            "attribute_id": attribute_id,
            "attribute_name": attribute.name,
            "options": [
                {
                    "id": opt.id,
                    "value": opt.value,
                    "additional_price": str(opt.additional_price),
                }
                for opt in options
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving attribute options | " f"Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute options.",
        )
