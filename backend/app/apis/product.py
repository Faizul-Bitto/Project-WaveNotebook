from fastapi import APIRouter, HTTPException, Path
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.product import Product
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.file import File

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_products(
    db: db_dependency, category_id: int = None, search: str = None, skip: int = 0, limit: int = 100
):
    """
    Retrieve all active products.
    GET /products
    """

    try:
        query = db.query(Product).filter(Product.is_active == True)

        if category_id:
            query = query.filter(Product.category_id == category_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(Product.name.ilike(search_term))

        products = query.offset(skip).limit(limit).all()
        total = query.count()

        result = []
        for product in products:
            # Get files
            files = db.query(File).filter(File.product_id == product.id).all()

            # Get attributes
            product_attrs = (
                db.query(ProductAttribute)
                .filter(ProductAttribute.product_id == product.id)
                .all()
            )

            # Get selected options for this product
            selected_options = (
                db.query(ProductAttributeOption)
                .filter(ProductAttributeOption.product_id == product.id)
                .all()
            )
            selected_option_ids = {so.option_id for so in selected_options}

            attributes = []
            for pa in product_attrs:
                attr = (
                    db.query(Attribute).filter(Attribute.id == pa.attribute_id).first()
                )

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
                            "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                    }
                )

            result.append(
                {
                    "id": product.id,
                    "product_code": product.product_code,
                    "name": product.name,
                    "slug": product.slug,
                    "category_id": product.category_id,
                    "base_price": str(product.base_price),
                    "description": product.description,
                    "is_in_stock": product.is_in_stock,
                    "files": [
                        {"id": f.id, "file_name": f.file_name, "file_url": f.file_url}
                        for f in files
                    ],
                    "attributes": attributes,
                }
            )

        logger.info(f"📦 Products Retrieved | Count={len(products)}")

        return {
            "message": "Products retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": result,
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving products | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products.",
        )


@router.get("/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_by_id(db: db_dependency, product_id: int = Path(gt=0)):
    """
    Retrieve a single product with full details.
    GET /products/{id}
    """

    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.is_active == True)
            .first()
        )

        if not product:
            logger.warning(f"⚠️ Product Not Found | ID={product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get files
        files = db.query(File).filter(File.product_id == product_id).all()

        # Get attributes
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
                            "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                }
            )

        logger.info(f"📦 Product Retrieved | ID={product.id}")

        return {
            "message": "Product retrieved successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "name": product.name,
                "slug": product.slug,
                "category_id": product.category_id,
                "base_price": str(product.base_price),
                "description": product.description,
                "specifications": product.specifications,
                "is_in_stock": product.is_in_stock,
                "files": [
                    {"id": f.id, "file_name": f.file_name, "file_url": f.file_url}
                    for f in files
                ],
                "attributes": attributes,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving product | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product.",
        )


@router.get("/slug/{product_slug}", status_code=status.HTTP_200_OK)
async def get_product_by_slug(db: db_dependency, product_slug: str):
    """
    Retrieve product by slug.
    GET /products/slug/{slug}
    """

    try:
        product = (
            db.query(Product)
            .filter(Product.slug == product_slug, Product.is_active == True)
            .first()
        )

        if not product:
            logger.warning(f"⚠️ Product Not Found | Slug={product_slug}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get files
        files = db.query(File).filter(File.product_id == product.id).all()

        # Get attributes
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product.id)
            .all()
        )

        # Get selected options for this product
        selected_options = (
            db.query(ProductAttributeOption)
            .filter(ProductAttributeOption.product_id == product.id)
            .all()
        )
        selected_option_ids = {so.option_id for so in selected_options}

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
                            "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                }
            )

        logger.info(f"📦 Product Retrieved | Slug={product_slug}")

        return {
            "message": "Product retrieved successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "name": product.name,
                "slug": product.slug,
                "category_id": product.category_id,
                "base_price": str(product.base_price),
                "description": product.description,
                "specifications": product.specifications,
                "is_in_stock": product.is_in_stock,
                "files": [
                    {"id": f.id, "file_name": f.file_name, "file_url": f.file_url}
                    for f in files
                ],
                "attributes": attributes,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving product | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product.",
        )
