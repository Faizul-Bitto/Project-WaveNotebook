import json
from fastapi import APIRouter, HTTPException, Path, Body
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.product import Product
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.product_variant import ProductVariant
from app.models.file import File
from app.utils.variant_generator import find_matching_variant, compute_product_in_stock

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_products(
    db: db_dependency, category_id: int = None, search: str = None, is_featured: bool = None, skip: int = 0, limit: int = 100
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

        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)

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
                                                            "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                    }
                )

            # Get price range from variants
            variants = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == product.id,
                    ProductVariant.is_active == True,
                )
                .all()
            )
            prices = [float(v.price) for v in variants if v.price is not None and float(v.price) > 0]
            price_range = None
            if prices:
                price_range = {
                    "min": str(min(prices)),
                    "max": str(max(prices)),
                }

            # Get selected_attributes of in-stock variants for frontend auto-selection
            in_stock_variants = []
            for v in variants:
                if v.stock_quantity > 0:
                    in_stock_variants.append(v.selected_attributes)

            result.append(
                {
                    "id": product.id,
                    "product_code": product.product_code,
                    "name": product.name,
                    "slug": product.slug,
                    "category_id": product.category_id,
                        "description": product.description,
                    "is_in_stock": compute_product_in_stock(db, product.id),
                    "is_featured": product.is_featured,
                    "price_range": price_range,
                    "files": [
                        {"id": f.id, "file_name": f.file_name, "file_url": f.file_url}
                        for f in files
                    ],
                    "attributes": attributes,
                    "in_stock_variants": in_stock_variants,
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
                                                        "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                }
            )

        # Get price range from variants
        variants = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.product_id == product_id,
                ProductVariant.is_active == True,
            )
            .all()
        )
        prices = [float(v.price) for v in variants if v.price is not None]
        price_range = None
        if prices:
            price_range = {
                "min": str(min(prices)),
                "max": str(max(prices)),
            }

        logger.info(f"📦 Product Retrieved | ID={product.id}")

        return {
            "message": "Product retrieved successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "name": product.name,
                "slug": product.slug,
                "category_id": product.category_id,
                "description": product.description,
                "specifications": product.specifications,
                "is_in_stock": compute_product_in_stock(db, product.id),
                "price_range": price_range,
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


@router.get("/{product_id}/default-variant", status_code=status.HTTP_200_OK)
async def get_default_variant(
    db: db_dependency,
    product_id: int = Path(gt=0),
):
    """
    Get the default variant for a product (preferably in-stock).
    GET /products/{product_id}/default-variant
    """
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.is_active == True)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # First try to find an in-stock variant
        variant = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.product_id == product_id,
                ProductVariant.is_active == True,
                ProductVariant.stock_quantity > 0,
            )
            .first()
        )

        # If no in-stock variant, get any active variant
        if not variant:
            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == product_id,
                    ProductVariant.is_active == True,
                )
                .first()
            )

        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No variants found for this product.",
            )

        in_stock = variant.stock_quantity > 0 and variant.is_active

        return {
            "message": "Default variant retrieved.",
            "variant": {
                "id": variant.id,
                "sku": variant.sku,
                "selected_attributes": json.loads(variant.selected_attributes),
                "price": str(variant.price) if variant.price is not None else None,
                "stock_quantity": variant.stock_quantity,
                "in_stock": in_stock,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting default variant | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get default variant.",
        )


@router.post("/find-variant", status_code=status.HTTP_200_OK)
async def find_variant(
    db: db_dependency,
    payload: dict = Body(...),
):
    """
    Find a variant by selected attributes.
    POST /products/find-variant
    Input: {"product_id": 1, "selected_attributes": {"Size": "A4", "Color": "Black"}}
    """
    try:
        product_id = payload.get("product_id")
        selected_attributes = payload.get("selected_attributes", {})

        if not product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="product_id is required.",
            )

        # Allow empty selected_attributes for products without attributes
        if not selected_attributes:
            selected_attributes = {}

        product = (
            db.query(Product)
            .filter(Product.id == product_id, Product.is_active == True)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        variant = find_matching_variant(db, product_id, selected_attributes)

        # If no matching variant found and no attributes were selected, return the single variant
        if not variant and not selected_attributes:
            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.product_id == product_id,
                    ProductVariant.is_active == True,
                )
                .first()
            )

        if not variant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Variant not available with selected attributes.",
            )

        in_stock = variant.stock_quantity > 0 and variant.is_active

        logger.info(
            f"✅ Variant Found | "
            f"Product={product_id} | "
            f"Variant={variant.id} | "
            f"SKU={variant.sku}"
        )

        return {
            "message": "Variant found.",
            "variant": {
                "id": variant.id,
                "sku": variant.sku,
                "selected_attributes": json.loads(variant.selected_attributes),
                "price": str(variant.price) if variant.price is not None else None,
                "stock_quantity": variant.stock_quantity,
                "in_stock": in_stock,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finding variant | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find variant.",
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
                                                        "is_selected": opt.id in selected_option_ids,
                        }
                        for opt in options
                        if opt.id in selected_option_ids
                    ],
                }
            )

        # Get price range from variants
        variants = (
            db.query(ProductVariant)
            .filter(
                ProductVariant.product_id == product.id,
                ProductVariant.is_active == True,
            )
            .all()
        )
        prices = [float(v.price) for v in variants if v.price is not None]
        price_range = None
        if prices:
            price_range = {
                "min": str(min(prices)),
                "max": str(max(prices)),
            }

        logger.info(f"📦 Product Retrieved | Slug={product_slug}")

        return {
            "message": "Product retrieved successfully.",
            "product": {
                "id": product.id,
                "product_code": product.product_code,
                "name": product.name,
                "slug": product.slug,
                "category_id": product.category_id,
                "description": product.description,
                "specifications": product.specifications,
                "is_in_stock": compute_product_in_stock(db, product.id),
                "price_range": price_range,
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
