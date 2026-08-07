import os
import json
import uuid
from datetime import datetime
from fastapi import (
    APIRouter,
    HTTPException,
    Path,
    Form,
    UploadFile,
    File as FastAPIFile,
)
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.product import Product
from app.models.category import Category
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.file import File
from app.utils.file_upload import upload_file_to_storage

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin - Products"],
)


def generate_slug(name: str) -> str:
    """
    Generate slug from product name.
    """
    import re

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
    db: db_dependency,
    admin: admin_dependency,
    category_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    specifications: str = Form(None),
    base_price: float = Form(...),
    is_in_stock: bool = Form(True),
    is_active: bool = Form(True),
    attributes: str = Form(...),
    files: list[UploadFile] = FastAPIFile(None),
):
    """
    Create product with attributes and multiple files.
    POST /admin/products
    """

    try:
        attributes_list = json.loads(attributes)

        # Generate product_code
        product_code = generate_product_code()
        while db.query(Product).filter(Product.product_code == product_code).first():
            product_code = generate_product_code()

        # Generate slug
        slug = generate_slug(name)
        existing_product = db.query(Product).filter(Product.slug == slug).first()

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product with this name already exists.",
            )

        # Check category exists
        category = db.query(Category).filter(Category.id == category_id).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
            )

        # Parse attributes with options
        # Format: [{"attribute_id": 1, "option_ids": [1, 2]}, ...]
        # Or backward compatible: [1, 2, 3] (just attribute IDs)
        parsed_attributes = []
        for item in attributes_list:
            if isinstance(item, dict):
                attr_id = item.get("attribute_id")
                option_ids = item.get("option_ids", [])
                if not attr_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Each attribute must have an attribute_id.",
                    )
                parsed_attributes.append(
                    {"attribute_id": attr_id, "option_ids": option_ids}
                )
            else:
                parsed_attributes.append(
                    {"attribute_id": item, "option_ids": []}
                )

        # Check all attributes exist
        for attr_data in parsed_attributes:
            attr = db.query(Attribute).filter(Attribute.id == attr_data["attribute_id"]).first()
            if not attr:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute ID {attr_data['attribute_id']} not found.",
                )

            # Check all options exist and belong to this attribute
            for option_id in attr_data["option_ids"]:
                option = (
                    db.query(AttributeOption)
                    .filter(
                        AttributeOption.id == option_id,
                        AttributeOption.attribute_id == attr_data["attribute_id"],
                    )
                    .first()
                )
                if not option:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Option ID {option_id} not found for attribute ID {attr_data['attribute_id']}.",
                    )

        # Create product
        new_product = Product(
            product_code=product_code,
            category_id=category_id,
            name=name,
            slug=slug,
            description=description,
            specifications=specifications,
            base_price=base_price,
            is_in_stock=is_in_stock,
            is_active=is_active,
        )

        db.add(new_product)
        db.flush()

        # Add attributes to product
        for attr_data in parsed_attributes:
            product_attr = ProductAttribute(
                product_id=new_product.id, attribute_id=attr_data["attribute_id"]
            )
            db.add(product_attr)

            # Add selected options for this attribute
            for option_id in attr_data["option_ids"]:
                product_attr_option = ProductAttributeOption(
                    product_id=new_product.id,
                    attribute_id=attr_data["attribute_id"],
                    option_id=option_id,
                )
                db.add(product_attr_option)

        db.flush()

        # Upload files if provided
        uploaded_files = []
        if files:
            for file in files:
                file_url = await upload_file_to_storage(file, new_product.id)

                if file_url:
                    new_file = File(
                        product_id=new_product.id,
                        file_name=file.filename,
                        file_url=file_url,
                    )
                    db.add(new_file)
                    uploaded_files.append(
                        {"file_name": file.filename, "file_url": file_url}
                    )

        db.commit()
        db.refresh(new_product)

        logger.info(
            f"✅ Product Created | "
            f"ID={new_product.id} | "
            f"Code={new_product.product_code} | "
            f"Files={len(uploaded_files)} | "
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
                "base_price": str(base_price),
                "description": description,
                "specifications": specifications,
                "is_in_stock": is_in_stock,
                "is_active": is_active,
                "attributes": parsed_attributes,
                "files": uploaded_files,
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
                    "category_name": next((c.name for c in db.query(Category).filter(Category.id == prod.category_id).all()), ""),
                    "name": prod.name,
                    "slug": prod.slug,
                    "base_price": str(prod.base_price),
                    "image_url": (db.query(File).filter(File.product_id == prod.id).first().file_url if db.query(File).filter(File.product_id == prod.id).first() else None),
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

        # Get attributes with selected options
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )

        # Get selected options for this product
        selected_options = (
            db.query(ProductAttributeOption)
            .filter(ProductAttributeOption.product_id == product_id)
            .all()
        )
        selected_option_ids = {so.option_id for so in selected_options}

        attributes = []
        for pa in product_attrs:
            attr = db.query(Attribute).filter(Attribute.id == pa.attribute_id).first()

            # Get all options for this attribute
            all_options = (
                db.query(AttributeOption)
                .filter(AttributeOption.attribute_id == pa.attribute_id)
                .all()
            )

            # Mark which options are selected for this product
            options = []
            for opt in all_options:
                options.append(
                    {
                        "id": opt.id,
                        "value": opt.value,
                        "additional_price": str(opt.additional_price),
                        "is_selected": opt.id in selected_option_ids,
                    }
                )

            attributes.append(
                {
                    "id": attr.id,
                    "name": attr.name,
                    "slug": attr.slug,
                    "options": options,
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
    category_id: int = Form(None),
    name: str = Form(None),
    description: str = Form(None),
    specifications: str = Form(None),
    base_price: float = Form(None),
    is_in_stock: bool = Form(None),
    is_active: bool = Form(None),
    attributes: str = Form(None),
    files: list[UploadFile] = FastAPIFile(None),
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
        if category_id:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Category not found."
                )
            product.category_id = category_id

        # Check new slug if name changed
        if name and name != product.name:
            new_slug = generate_slug(name)
            existing = db.query(Product).filter(Product.slug == new_slug).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product with this name already exists.",
                )
            product.slug = new_slug
            product.name = name

        # Update attributes if provided
        if attributes:
            attributes_list = json.loads(attributes)

            # Parse attributes with options
            # Format: [{"attribute_id": 1, "option_ids": [1, 2]}, ...]
            # Or backward compatible: [1, 2, 3] (just attribute IDs)
            parsed_attributes = []
            for item in attributes_list:
                if isinstance(item, dict):
                    attr_id = item.get("attribute_id")
                    option_ids = item.get("option_ids", [])
                    if not attr_id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Each attribute must have an attribute_id.",
                        )
                    parsed_attributes.append(
                        {"attribute_id": attr_id, "option_ids": option_ids}
                    )
                else:
                    parsed_attributes.append(
                        {"attribute_id": item, "option_ids": []}
                    )

            # Check all attributes exist
            for attr_data in parsed_attributes:
                attr = db.query(Attribute).filter(Attribute.id == attr_data["attribute_id"]).first()
                if not attr:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Attribute ID {attr_data['attribute_id']} not found.",
                    )

                # Check all options exist and belong to this attribute
                for option_id in attr_data["option_ids"]:
                    option = (
                        db.query(AttributeOption)
                        .filter(
                            AttributeOption.id == option_id,
                            AttributeOption.attribute_id == attr_data["attribute_id"],
                        )
                        .first()
                    )
                    if not option:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Option ID {option_id} not found for attribute ID {attr_data['attribute_id']}.",
                        )

            # Remove old attributes and their selected options
            db.query(ProductAttribute).filter(
                ProductAttribute.product_id == product_id
            ).delete()
            db.query(ProductAttributeOption).filter(
                ProductAttributeOption.product_id == product_id
            ).delete()

            # Add new attributes with selected options
            for attr_data in parsed_attributes:
                product_attr = ProductAttribute(
                    product_id=product_id, attribute_id=attr_data["attribute_id"]
                )
                db.add(product_attr)

                # Add selected options for this attribute
                for option_id in attr_data["option_ids"]:
                    product_attr_option = ProductAttributeOption(
                        product_id=product_id,
                        attribute_id=attr_data["attribute_id"],
                        option_id=option_id,
                    )
                    db.add(product_attr_option)

        # Upload new files if provided
        if files:
            for file in files:
                file_url = await upload_file_to_storage(file, product_id)
                if file_url:
                    new_file = File(
                        product_id=product_id,
                        file_name=file.filename,
                        file_url=file_url,
                    )
                    db.add(new_file)

        # Update other fields
        if description is not None:
            product.description = description
        if specifications is not None:
            product.specifications = specifications
        if base_price is not None:
            product.base_price = base_price
        if is_in_stock is not None:
            product.is_in_stock = is_in_stock
        if is_active is not None:
            product.is_active = is_active

        db.commit()
        db.refresh(product)

        logger.info(
            f"✅ Product Updated | " f"ID={product.id} | " f"Admin={admin.phone_number}"
        )

        # Get updated attributes with selected options
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )

        # Get selected options for this product
        selected_options = (
            db.query(ProductAttributeOption)
            .filter(ProductAttributeOption.product_id == product_id)
            .all()
        )
        selected_option_ids = {so.option_id for so in selected_options}

        attributes = []
        for pa in product_attrs:
            attr = db.query(Attribute).filter(Attribute.id == pa.attribute_id).first()

            # Get all options for this attribute
            all_options = (
                db.query(AttributeOption)
                .filter(AttributeOption.attribute_id == pa.attribute_id)
                .all()
            )

            options = []
            for opt in all_options:
                options.append(
                    {
                        "id": opt.id,
                        "value": opt.value,
                        "additional_price": str(opt.additional_price),
                        "is_selected": opt.id in selected_option_ids,
                    }
                )

            attributes.append(
                {
                    "id": attr.id,
                    "name": attr.name,
                    "slug": attr.slug,
                    "options": options,
                }
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
                "attributes": attributes,
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
