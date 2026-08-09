# app/apis/admin/categories.py
import re
from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate

router = APIRouter(
    prefix="/admin/categories",
    tags=["Admin - Categories"],
)


def generate_slug(name: str) -> str:
    """
    Generate slug from category name.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    db: db_dependency, admin: admin_dependency, category_data: CategoryCreate
):
    """
    Create a new category (admin only).
    POST /admin/categories
    """

    try:
        # Generate slug from name
        slug = generate_slug(category_data.name)

        # Check if slug already exists
        existing_category = db.query(Category).filter(Category.slug == slug).first()

        if existing_category:
            logger.warning(
                f"⚠️ Category Creation Failed | "
                f"Slug={slug} already exists | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category with this name already exists.",
            )

        parent_id = (
            category_data.parent_id
            if category_data.parent_id and category_data.parent_id > 0
            else None
        )

        if parent_id:
            parent_category = (
                db.query(Category).filter(Category.id == parent_id).first()
            )

            if not parent_category:
                logger.warning(
                    f"⚠️ Category Creation Failed | "
                    f"Parent ID={parent_id} not found | "
                    f"Admin={admin.phone_number}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found.",
                )

        new_category = Category(
            name=category_data.name,
            slug=slug,
            parent_id=parent_id,
            description=category_data.description,
            is_active=category_data.is_active,
            image_url=category_data.image_url,
        )

        db.add(new_category)
        db.commit()
        db.refresh(new_category)

        logger.info(
            f"✅ Category Created | "
            f"ID={new_category.id} | "
            f"Name={new_category.name} | "
            f"Slug={new_category.slug} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Category created successfully.",
            "category": {
                "id": new_category.id,
                "name": new_category.name,
                "slug": new_category.slug,
                "parent_id": new_category.parent_id,
                "description": new_category.description,
                "is_active": new_category.is_active,
                "created_at": new_category.created_at.isoformat(),
                "updated_at": new_category.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Category Creation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create category.",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_categories(
    db: db_dependency,
    admin: admin_dependency,
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
):
    """
    Get all categories (active + inactive) for admin.
    GET /admin/categories
    """

    try:
        query = db.query(Category)

        if is_active is not None:
            query = query.filter(Category.is_active == is_active)

        categories = query.offset(skip).limit(limit).all()
        total = db.query(Category).count()

        logger.info(
            f"📂 Categories Retrieved | "
            f"Count={len(categories)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Categories retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "slug": cat.slug,
                    "parent_id": cat.parent_id,
                    "description": cat.description,
                    "is_active": cat.is_active,
                    "created_at": cat.created_at.isoformat(),
                    "updated_at": cat.updated_at.isoformat(),
                }
                for cat in categories
            ],
        }

    except Exception as e:
        logger.error(
            f"❌ Error retrieving categories | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories.",
        )


@router.get("/{category_id}", status_code=status.HTTP_200_OK)
async def get_category_by_id(
    db: db_dependency, admin: admin_dependency, category_id: int = Path(gt=0)
):
    """
    Get single category details.
    GET /admin/categories/{id}
    """

    try:
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            logger.warning(
                f"⚠️ Category Not Found | "
                f"ID={category_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        parent = None
        if category.parent_id:
            parent = (
                db.query(Category).filter(Category.id == category.parent_id).first()
            )

        children = db.query(Category).filter(Category.parent_id == category.id).all()

        logger.info(
            f"📂 Category Retrieved | "
            f"ID={category.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Category retrieved successfully.",
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "parent_id": category.parent_id,
                "description": category.description,
                "is_active": category.is_active,
                "parent": (
                    {"id": parent.id, "name": parent.name, "slug": parent.slug}
                    if parent
                    else None
                ),
                "children": [
                    {"id": child.id, "name": child.name, "slug": child.slug}
                    for child in children
                ],
                "created_at": category.created_at.isoformat(),
                "updated_at": category.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving category | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve category.",
        )


@router.put("/{category_id}", status_code=status.HTTP_200_OK)
async def update_category(
    db: db_dependency,
    admin: admin_dependency,
    category_id: int = Path(gt=0),
    category_data: CategoryUpdate = None,
):
    """
    Update category details.
    PUT /admin/categories/{id}
    """

    try:
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            logger.warning(
                f"⚠️ Category Not Found | "
                f"ID={category_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        # If name is updated, regenerate slug (unless custom slug provided)
        if category_data.name and category_data.name != category.name:
            if not category_data.slug:
                category_data.slug = generate_slug(category_data.name)

        # Check if new slug already exists
        if category_data.slug and category_data.slug != category.slug:
            existing = (
                db.query(Category).filter(Category.slug == category_data.slug).first()
            )

            if existing:
                logger.warning(
                    f"⚠️ Category Update Failed | "
                    f"Slug={category_data.slug} already exists | "
                    f"Admin={admin.phone_number}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Category with this slug already exists.",
                )

        if category_data.parent_id and category_data.parent_id != category.parent_id:
            if category_data.parent_id == category_id:
                logger.warning(
                    f"⚠️ Category Update Failed | "
                    f"Cannot set category as its own parent | "
                    f"Admin={admin.phone_number}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent.",
                )

            parent = (
                db.query(Category)
                .filter(Category.id == category_data.parent_id)
                .first()
            )

            if not parent:
                logger.warning(
                    f"⚠️ Category Update Failed | "
                    f"Parent ID={category_data.parent_id} not found | "
                    f"Admin={admin.phone_number}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found.",
                )

        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        db.commit()
        db.refresh(category)

        logger.info(
            f"✅ Category Updated | "
            f"ID={category.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Category updated successfully.",
            "category": {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "parent_id": category.parent_id,
                "description": category.description,
                "is_active": category.is_active,
                "created_at": category.created_at.isoformat(),
                "updated_at": category.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Category Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update category.",
        )


@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
async def delete_category(
    db: db_dependency, admin: admin_dependency, category_id: int = Path(gt=0)
):
    """
    Delete category and cascade delete products.
    DELETE /admin/categories/{id}
    """

    try:
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            logger.warning(
                f"⚠️ Category Delete Failed | "
                f"ID={category_id} not found | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        category_name = category.name

        db.delete(category)
        db.commit()

        logger.info(
            f"✅ Category Deleted | "
            f"ID={category_id} | "
            f"Name={category_name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Category deleted successfully.",
            "deleted_category_id": category_id,
            "deleted_category_name": category_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Category Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete category.",
        )


@router.get("/{category_id}/products", status_code=status.HTTP_200_OK)
async def get_category_products(
    db: db_dependency,
    admin: admin_dependency,
    category_id: int = Path(gt=0),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all products in a specific category.
    GET /admin/categories/{id}/products
    """

    try:
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            logger.warning(
                f"⚠️ Category Not Found | "
                f"ID={category_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        from app.models.product import Product

        products = (
            db.query(Product)
            .filter(Product.category_id == category_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        total = db.query(Product).filter(Product.category_id == category_id).count()

        logger.info(
            f"📦 Category Products Retrieved | "
            f"Category ID={category_id} | "
            f"Count={len(products)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Products retrieved successfully.",
            "category_id": category_id,
            "category_name": category.name,
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "slug": product.slug,
                    "base_price": str(product.base_price),
                    "is_in_stock": product.is_in_stock,
                    "is_active": product.is_active,
                    "created_at": product.created_at.isoformat(),
                }
                for product in products
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving category products | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products.",
        )
