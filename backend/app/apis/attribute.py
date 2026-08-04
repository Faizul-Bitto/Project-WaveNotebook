from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption

router = APIRouter(
    prefix="/attributes",
    tags=["Attributes"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_attributes(db: db_dependency):
    """
    Retrieve all active attributes with options.
    GET /attributes
    """

    try:
        attributes = db.query(Attribute).filter(Attribute.is_active == True).all()

        if not attributes:
            logger.info("📋 No Active Attributes Found")
            return {"message": "No active attributes found.", "attributes": []}

        result = []
        for attr in attributes:
            options = (
                db.query(AttributeOption)
                .filter(AttributeOption.attribute_id == attr.id)
                .all()
            )

            result.append(
                {
                    "id": attr.id,
                    "name": attr.name,
                    "slug": attr.slug,
                    "options": [
                        {
                            "id": opt.id,
                            "value": opt.value,
                            "additional_price": str(opt.additional_price),
                        }
                        for opt in options
                    ],
                }
            )

        logger.info(f"📋 Attributes Retrieved | Count={len(attributes)}")

        return {"message": "Attributes retrieved successfully.", "attributes": result}

    except Exception as e:
        logger.error(f"❌ Error retrieving attributes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attributes.",
        )


@router.get("/{attribute_id}", status_code=status.HTTP_200_OK)
async def get_attribute_by_id(db: db_dependency, attribute_id: int = Path(gt=0)):
    """
    Retrieve a single attribute with options by ID.
    GET /attributes/{id}
    """

    try:
        attribute = (
            db.query(Attribute)
            .filter(Attribute.id == attribute_id, Attribute.is_active == True)
            .first()
        )

        if not attribute:
            logger.warning(f"⚠️ Attribute Not Found | ID={attribute_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        options = (
            db.query(AttributeOption)
            .filter(AttributeOption.attribute_id == attribute_id)
            .all()
        )

        logger.info(f"📋 Attribute Retrieved | ID={attribute_id}")

        return {
            "message": "Attribute retrieved successfully.",
            "attribute": {
                "id": attribute.id,
                "name": attribute.name,
                "slug": attribute.slug,
                "options": [
                    {
                        "id": opt.id,
                        "value": opt.value,
                        "additional_price": str(opt.additional_price),
                    }
                    for opt in options
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute.",
        )


@router.get("/slug/{attribute_slug}", status_code=status.HTTP_200_OK)
async def get_attribute_by_slug(db: db_dependency, attribute_slug: str):
    """
    Retrieve attribute by slug.
    GET /attributes/slug/{slug}
    """

    try:
        attribute = (
            db.query(Attribute)
            .filter(Attribute.slug == attribute_slug, Attribute.is_active == True)
            .first()
        )

        if not attribute:
            logger.warning(f"⚠️ Attribute Not Found | Slug={attribute_slug}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found."
            )

        options = (
            db.query(AttributeOption)
            .filter(AttributeOption.attribute_id == attribute.id)
            .all()
        )

        logger.info(f"📋 Attribute Retrieved | Slug={attribute_slug}")

        return {
            "message": "Attribute retrieved successfully.",
            "attribute": {
                "id": attribute.id,
                "name": attribute.name,
                "slug": attribute.slug,
                "options": [
                    {
                        "id": opt.id,
                        "value": opt.value,
                        "additional_price": str(opt.additional_price),
                    }
                    for opt in options
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving attribute: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attribute.",
        )
