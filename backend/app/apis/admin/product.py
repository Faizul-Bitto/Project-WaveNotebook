import re
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.product import Product
from app.models.category import Category
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.file import File
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.file import FileCreate, FileUpdate

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin - Products"],
)


def generate_slug(name: str) -> str:
    """
    Generate slug from product name.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


def generate_product_code() -> str:
    """
    Generate unique product code.
    Format: PROD-YYYYMMDD-XXXXX
    """
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = str(uuid.uuid4()).replace("-", "").upper()[:5]
    return f"PROD-{date_str}-{random_str}"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_product(
    db: db_dependency, admin: admin_dependency, product_data: ProductCreate
):
    """
    Create a new product with attributes (admin only).
    POST /admin/products
    """

    try:
        # Generate product_code
        product_code = generate_product_code()
        while db.query(Product).filter(Product.product_code == product_code).first():
            product_code = generate_product_code()

        # Generate slug
        slug = generate_slug(product_data.name)
        existing_product = db.query(Product).filter(Product.slug == slug).first()

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this name already exists.",
            )

        # Check category exists
        category = (
            db.query(Category).filter(Category.id == product_data.category_id).first()
        )

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        # Check all attributes exist
        for attr_id in product_data.attributes:
            attr = db.query(Attribute).filter(Attribute.id == attr_id).first()
            if not attr:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute ID {attr_id} not found.",
                )

        # Create product
        new_product = Product(
            product_code=product_code,
            category_id=product_data.category_id,
            name=product_data.name,
            slug=slug,
            description=product_data.description,
            specifications=product_data.specifications,
            base_price=product_data.base_price,
            is_in_stock=product_data.is_in_stock,
            is_active=product_data.is_active,
        )

        db.add(new_product)
        db.flush()  # Get product ID

        # Add attributes to product
        for attr_id in product_data.attributes:
            product_attr = ProductAttribute(
                product_id=new_product.id, attribute_id=attr_id
            )
            db.add(product_attr)

        db.commit()
        db.refresh(new_product)

        logger.info(
            f"✅ Product Created | "
            f"ID={new_product.id} | "
            f"Code={new_product.product_code} | "
            f"Name={new_product.name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Product created successfully.",
            "product": {
                "id": new_product.id,
                "product_code": new_product.product_code,
                "category_id": new_product.category_id,
                "name": new_product.name,
                "slug": new_product.slug,
                "base_price": str(new_product.base_price),
                "description": new_product.description,
                "specifications": new_product.specifications,
                "is_in_stock": new_product.is_in_stock,
                "is_active": new_product.is_active,
                "attributes": product_data.attributes,
                "created_at": new_product.created_at.isoformat(),
                "updated_at": new_product.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product Creation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product.",
        )


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_products(
    db: db_dependency,
    admin: admin_dependency,
    category_id: int = None,
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
):
    """
    Get all products (active + inactive) for admin.
    GET /admin/products
    """

    try:
        query = db.query(Product)

        if category_id:
            query = query.filter(Product.category_id == category_id)

        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        products = query.offset(skip).limit(limit).all()
        total = db.query(Product).count()

        logger.info(
            f"📦 Products Retrieved | "
            f"Count={len(products)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Products retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": [
                {
                    "id": prod.id,
                    "product_code": prod.product_code,
                    "category_id": prod.category_id,
                    "name": prod.name,
                    "slug": prod.slug,
                    "base_price": str(prod.base_price),
                    "is_in_stock": prod.is_in_stock,
                    "is_active": prod.is_active,
                    "created_at": prod.created_at.isoformat(),
                    "updated_at": prod.updated_at.isoformat(),
                }
                for prod in products
            ],
        }

    except Exception as e:
        logger.error(
            f"❌ Error retrieving products | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products.",
        )


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_by_id(
    db: db_dependency, admin: admin_dependency, product_id: int = Path(gt=0)
):
    """
    Get single product details with attributes and files.
    GET /admin/products/{id}
    """

    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            logger.warning(
                f"⚠️ Product Not Found | "
                f"ID={product_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get files
        files = db.query(File).filter(File.product_id == product_id).all()

        # Get attributes with options
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )

        attributes = []
        for pa in product_attrs:
            attr = db.query(Attribute).filter(Attribute.id == pa.attribute_id).first()

            options = (
                db.query(AttributeOption)
                .filter(AttributeOption.attribute_id == pa.attribute_id)
                .all()
            )

            attributes.append(
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

        logger.info(
            f"📦 Product Retrieved | "
            f"ID={product.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Product retrieved successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "category_id": product.category_id,
                "name": product.name,
                "slug": product.slug,
                "description": product.description,
                "specifications": product.specifications,
                "base_price": str(product.base_price),
                "is_in_stock": product.is_in_stock,
                "is_active": product.is_active,
                "files": [
                    {"id": f.id, "file_name": f.file_name, "file_url": f.file_url}
                    for f in files
                ],
                "attributes": attributes,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving product | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product.",
        )


@router.put("/{product_id}", status_code=status.HTTP_200_OK)
async def update_product(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    product_data: ProductUpdate = None,
):
    """
    Update product details and attributes.
    PUT /admin/products/{id}
    """

    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            logger.warning(
                f"⚠️ Product Not Found | "
                f"ID={product_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Check category exists
        if product_data.category_id:
            category = (
                db.query(Category)
                .filter(Category.id == product_data.category_id)
                .first()
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
                )

        # Check new slug if name changed
        if product_data.name and product_data.name != product.name:
            new_slug = generate_slug(product_data.name)
            existing = db.query(Product).filter(Product.slug == new_slug).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this name already exists.",
                )
            product.slug = new_slug

        # Update attributes if provided
        if product_data.attributes is not None:
            # Check all attributes exist
            for attr_id in product_data.attributes:
                attr = db.query(Attribute).filter(Attribute.id == attr_id).first()
                if not attr:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Attribute ID {attr_id} not found.",
                    )

            # Remove old attributes
            db.query(ProductAttribute).filter(
                ProductAttribute.product_id == product_id
            ).delete()

            # Add new attributes
            for attr_id in product_data.attributes:
                product_attr = ProductAttribute(
                    product_id=product_id, attribute_id=attr_id
                )
                db.add(product_attr)

        # Update other fields
        update_data = product_data.model_dump(exclude_unset=True)
        update_data.pop("attributes", None)  # Remove attributes from update

        for field, value in update_data.items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)

        logger.info(
            f"✅ Product Updated | " f"ID={product.id} | " f"Admin={admin.phone_number}"
        )

        return {
            "message": "Product updated successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "category_id": product.category_id,
                "name": product.name,
                "slug": product.slug,
                "base_price": str(product.base_price),
                "description": product.description,
                "specifications": product.specifications,
                "is_in_stock": product.is_in_stock,
                "is_active": product.is_active,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product.",
        )


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    db: db_dependency, admin: admin_dependency, product_id: int = Path(gt=0)
):
    """
    Delete product (cascade delete files and attributes).
    DELETE /admin/products/{id}
    """

    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            logger.warning(
                f"⚠️ Product Delete Failed | "
                f"ID={product_id} not found | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        product_name = product.name

        db.delete(product)
        db.commit()

        logger.info(
            f"✅ Product Deleted | "
            f"ID={product_id} | "
            f"Name={product_name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Product deleted successfully.",
            "deleted_product_id": product_id,
            "deleted_product_name": product_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product.",
        )


@router.post("/{product_id}/files", status_code=status.HTTP_201_CREATED)
async def add_product_file(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    file_data: FileCreate = None,
):
    """
    Add file to product.
    POST /admin/products/{id}/files
    """

    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        new_file = File(
            product_id=product_id,
            file_name=file_data.file_name,
            file_url=file_data.file_url,
        )

        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        logger.info(
            f"✅ Product File Added | "
            f"Product ID={product_id} | "
            f"File={file_data.file_name} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File added successfully.",
            "file": {
                "id": new_file.id,
                "file_name": new_file.file_name,
                "file_url": new_file.file_url,
                "created_at": new_file.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product File Addition Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add file.",
        )


@router.put("/{product_id}/files/{file_id}", status_code=status.HTTP_200_OK)
async def update_product_file(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    file_id: int = Path(gt=0),
    file_data: FileUpdate = None,
):
    """
    Update product file.
    PUT /admin/products/{id}/files/{file_id}
    """

    try:
        file = (
            db.query(File)
            .filter(File.id == file_id, File.product_id == product_id)
            .first()
        )

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        update_data = file_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(file, field, value)

        db.commit()
        db.refresh(file)

        logger.info(
            f"✅ Product File Updated | "
            f"Product ID={product_id} | "
            f"File ID={file_id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File updated successfully.",
            "file": {
                "id": file.id,
                "file_name": file.file_name,
                "file_url": file.file_url,
                "created_at": file.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product File Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file.",
        )


@router.delete("/{product_id}/files/{file_id}", status_code=status.HTTP_200_OK)
async def delete_product_file(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    file_id: int = Path(gt=0),
):
    """
    Delete product file.
    DELETE /admin/products/{id}/files/{file_id}
    """

    try:
        file = (
            db.query(File)
            .filter(File.id == file_id, File.product_id == product_id)
            .first()
        )

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
            )

        file_name = file.file_name

        db.delete(file)
        db.commit()

        logger.info(
            f"✅ Product File Deleted | "
            f"Product ID={product_id} | "
            f"File ID={file_id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "File deleted successfully.",
            "deleted_file_id": file_id,
            "deleted_file_name": file_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Product File Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file.",
        )
