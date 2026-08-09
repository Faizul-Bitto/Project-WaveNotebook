from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.category import Category

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)


def build_category_tree(categories, parent_id=None):
    """
    Build nested category tree structure.
    """
    tree = []
    for category in categories:
        if category.parent_id == parent_id:
            tree.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "slug": category.slug,
                    "description": category.description,
                    "image_url": category.image_url,
                    "children": build_category_tree(categories, category.id),
                }
            )
    return tree


@router.get("", status_code=status.HTTP_200_OK)
async def get_categories(db: db_dependency):
    """
    Retrieve all active categories in hierarchical tree structure.
    GET /categories
    """

    try:
        categories = db.query(Category).filter(Category.is_active == True).all()

        if not categories:
            logger.info("📂 No Active Categories Found")
            return {"message": "No active categories found.", "categories": []}

        tree = build_category_tree(categories)

        logger.info(f"📂 Categories Retrieved | Count={len(categories)}")

        return {"message": "Categories retrieved successfully.", "categories": tree}

    except Exception as e:
        logger.error(f"❌ Error retrieving categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories.",
        )


@router.get("/{category_id}", status_code=status.HTTP_200_OK)
async def get_category_by_id(db: db_dependency, category_id: int = Path(gt=0)):
    """
    Retrieve a single category with its subcategories by ID.
    GET /categories/{id}
    """

    try:
        category = (
            db.query(Category)
            .filter(Category.id == category_id, Category.is_active == True)
            .first()
        )

        if not category:
            logger.warning(f"⚠️ Category Not Found | ID={category_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        all_categories = db.query(Category).filter(Category.is_active == True).all()

        children = build_category_tree(all_categories, category.id)

        logger.info(f"📂 Category Retrieved | ID={category_id}")

        return {
            "message": "Category retrieved successfully.",
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "children": children,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category.",
        )


@router.get("/slug/{category_slug}", status_code=status.HTTP_200_OK)
async def get_category_by_slug(db: db_dependency, category_slug: str):
    """
    Retrieve a category by its slug (for SEO URLs).
    GET /categories/slug/{slug}
    """

    try:
        category = (
            db.query(Category)
            .filter(Category.slug == category_slug, Category.is_active == True)
            .first()
        )

        if not category:
            logger.warning(f"⚠️ Category Not Found | Slug={category_slug}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        all_categories = db.query(Category).filter(Category.is_active == True).all()

        children = build_category_tree(all_categories, category.id)

        logger.info(f"📂 Category Retrieved | Slug={category_slug}")

        return {
            "message": "Category retrieved successfully.",
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "children": children,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving category: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category.",
        )
