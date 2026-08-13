import json
from fastapi import APIRouter, HTTPException, Path, Body
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.order_item import OrderItem
from app.utils.variant_generator import (
    generate_variant_combinations,
    build_sku,
    selected_attributes_to_key,
)

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin - Product Variants"],
)


@router.get("/{product_id}/variants", status_code=status.HTTP_200_OK)
async def get_product_variants(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
):
    """
    Get all variants for a product.
    GET /admin/products/{product_id}/variants
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .order_by(ProductVariant.id)
            .all()
        )

        result = []
        for variant in variants:
            try:
                selected_attrs = json.loads(variant.selected_attributes)
            except json.JSONDecodeError:
                selected_attrs = {}

            result.append(
                {
                    "id": variant.id,
                    "sku": variant.sku,
                    "selected_attributes": selected_attrs,
                    "price": str(variant.price) if variant.price is not None else None,
                    "stock_quantity": variant.stock_quantity,
                    "is_active": variant.is_active,
                    "price_status": "filled" if variant.price is not None and float(variant.price) > 0 else "empty",
                    "created_at": variant.created_at.isoformat(),
                    "updated_at": variant.updated_at.isoformat(),
                }
            )

        logger.info(
            f"✅ Variants Retrieved | "
            f"Product={product_id} | "
            f"Count={len(result)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Variants retrieved.",
            "product_id": product_id,
            "product_name": product.name,
            "total_variants": len(result),
            "variants": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving variants | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve variants.",
        )


@router.put("/variants/{variant_id}", status_code=status.HTTP_200_OK)
async def update_variant(
    db: db_dependency,
    admin: admin_dependency,
    variant_id: int = Path(gt=0),
    price: float = Body(None),
     stock_quantity: int = Body(None),
     is_active: bool = Body(None),
 ):
    """
    Update a single variant.
    PUT /admin/products/variants/{variant_id}
    """
    try:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found."
            )

        if price is not None:
            variant.price = price
        if stock_quantity is not None:
            variant.stock_quantity = stock_quantity
        if is_active is not None:
            variant.is_active = is_active

        db.commit()
        db.refresh(variant)

        logger.info(
            f"✅ Variant Updated | "
            f"ID={variant.id} | "
            f"SKU={variant.sku} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Variant updated successfully.",
            "variant": {
                "id": variant.id,
                "sku": variant.sku,
                "price": str(variant.price) if variant.price is not None else None,
                "stock_quantity": variant.stock_quantity,
                "is_active": variant.is_active,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Variant Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update variant.",
        )


@router.put("/{product_id}/variants/bulk", status_code=status.HTTP_200_OK)
async def bulk_update_variants(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    updates: dict = Body(...),
):
    """
    Bulk update multiple variants.
    PUT /admin/products/{product_id}/variants/bulk
     Input: {"1": {"price": 250, "stock_quantity": 10}, ...}
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        updated_count = 0
        for variant_id_str, data in updates.items():
            try:
                variant_id = int(variant_id_str)
            except (ValueError, TypeError):
                continue

            variant = (
                db.query(ProductVariant)
                .filter(
                    ProductVariant.id == variant_id,
                    ProductVariant.product_id == product_id,
                )
                .first()
            )
            if not variant:
                continue

            if "price" in data and data["price"] is not None:
                variant.price = data["price"]
            if "stock_quantity" in data and data["stock_quantity"] is not None:
                variant.stock_quantity = data["stock_quantity"]
            if "is_active" in data and data["is_active"] is not None:
                variant.is_active = data["is_active"]

            updated_count += 1

        db.commit()

        logger.info(
            f"✅ Bulk Variants Updated | "
            f"Product={product_id} | "
            f"Count={updated_count} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": f"Updated {updated_count} variants successfully.",
            "product_id": product_id,
            "updated_count": updated_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Bulk Variants Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update variants.",
        )


@router.post("/{product_id}/variants/generate", status_code=status.HTTP_201_CREATED)
async def generate_variants(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    attribute_option_ids: list[int] = Body(default=None),
):
    """
    Generate variants from selected attribute options.
    Creates new variants, keeps existing ones, and removes variants for unselected options.
    POST /admin/products/{product_id}/variants/generate
    Input (optional): [1, 2, 3, 4] (selected option IDs to set on the product)
    If no body is provided, generates variants from the product's existing selected options.
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get all product attributes
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )
        attribute_ids = [pa.attribute_id for pa in product_attrs]

        # Get all selected options for this product
        selected_options = (
            db.query(ProductAttributeOption)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )
        selected_option_ids = {so.option_id for so in selected_options}

        # If attribute_option_ids provided, update selected options to match
        if attribute_option_ids is not None:
            # Remove options that are no longer selected
            for so in selected_options:
                if so.option_id not in attribute_option_ids:
                    db.delete(so)

            # Add new options that weren't selected before
            existing_option_ids = {so.option_id for so in selected_options}
            for option_id in attribute_option_ids:
                if option_id not in existing_option_ids:
                    # Find which attribute this option belongs to
                    option = db.query(AttributeOption).filter(AttributeOption.id == option_id).first()
                    if option:
                        new_so = ProductAttributeOption(
                            product_id=product_id,
                            attribute_id=option.attribute_id,
                            option_id=option_id,
                        )
                        db.add(new_so)

            db.flush()

            selected_option_ids = set(attribute_option_ids)

        # Get all existing variants
        existing_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .all()
        )
        existing_keys = set()
        for variant in existing_variants:
            try:
                attrs = json.loads(variant.selected_attributes)
                existing_keys.add(selected_attributes_to_key(attrs))
            except json.JSONDecodeError:
                continue

        # If no attributes or no selected options, create a single default variant
        if not attribute_ids or not selected_option_ids:
            # Check if a default variant already exists
            default_variant = (
                db.query(ProductVariant)
                .filter(ProductVariant.product_id == product_id)
                .first()
            )
            if not default_variant:
                sku = f"{product.product_code}-DEFAULT"
                new_variant = ProductVariant(
                    product_id=product_id,
                    sku=sku,
                    selected_attributes=json.dumps({}),
                     price=0,
                    stock_quantity=0,
                    is_active=True,
                )
                db.add(new_variant)
                db.commit()

                return {
                    "message": "Generated 1 default variant.",
                    "product_id": product_id,
                    "new_variants_count": 1,
                    "removed_variants_count": 0,
                    "total_variants_now": 1,
                }
            return {
                "message": "Default variant already exists.",
                "product_id": product_id,
                "new_variants_count": 0,
                "removed_variants_count": 0,
                "total_variants_now": 1,
            }

        # Generate all combinations from selected options
        combinations = await generate_variant_combinations(db, attribute_ids, product_id)

        # Create new variants that don't exist yet
        new_variants_count = 0
        for combo in combinations:
            key = selected_attributes_to_key(combo["selected_attributes"])
            if key not in existing_keys:
                sku = build_sku(product.product_code, combo["selected_attributes"])

                # Check SKU doesn't already exist
                existing_sku = (
                    db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
                )
                if existing_sku:
                    continue

                new_variant = ProductVariant(
                    product_id=product_id,
                    sku=sku,
                    selected_attributes=json.dumps(combo["selected_attributes"]),
                     price=0,
                    stock_quantity=0,
                    is_active=True,
                )
                db.add(new_variant)
                new_variants_count += 1

        # Remove variants that no longer match any combination
        valid_keys = {selected_attributes_to_key(c["selected_attributes"]) for c in combinations}
        removed_count = 0
        for variant in existing_variants:
            try:
                attrs = json.loads(variant.selected_attributes)
                key = selected_attributes_to_key(attrs)
                if key not in valid_keys:
                    db.delete(variant)
                    removed_count += 1
            except json.JSONDecodeError:
                continue

        db.commit()

        total_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .count()
        )

        logger.info(
            f"✅ Variants Generated | "
            f"Product={product_id} | "
            f"New={new_variants_count} | "
            f"Removed={removed_count} | "
            f"Total={total_variants} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": f"Generated {new_variants_count} new variants, removed {removed_count}.",
            "product_id": product_id,
            "new_variants_count": new_variants_count,
            "removed_variants_count": removed_count,
            "total_variants_now": total_variants,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Variants Generation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate variants.",
        )


@router.post("/{product_id}/variants", status_code=status.HTTP_201_CREATED)
async def add_new_variants(
    db: db_dependency,
    admin: admin_dependency,
    product_id: int = Path(gt=0),
    new_attribute_option_ids: list[int] = Body(...),
):
    """
    Add new variants when new attribute options are added to a product.
    Adds the new options to the product's selected options, then generates
    only the new variant combinations. Existing variants are preserved.
    POST /admin/products/{product_id}/variants
    Input: [1, 2, 4] (new option IDs to add)
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        # Get all product attributes
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == product_id)
            .all()
        )
        attribute_ids = [pa.attribute_id for pa in product_attrs]

        # Get all currently selected options for this product
        selected_options = (
            db.query(ProductAttributeOption)
            .filter(ProductAttributeOption.product_id == product_id)
            .all()
        )
        selected_option_ids = {so.option_id for so in selected_options}

        # Add new option IDs to ProductAttributeOption (if not already there)
        for option_id in new_attribute_option_ids:
            if option_id not in selected_option_ids:
                option = db.query(AttributeOption).filter(AttributeOption.id == option_id).first()
                if option:
                    new_so = ProductAttributeOption(
                        product_id=product_id,
                        attribute_id=option.attribute_id,
                        option_id=option_id,
                    )
                    db.add(new_so)

        db.flush()

        # Get all existing variant attribute combinations
        existing_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .all()
        )
        existing_keys = set()
        for variant in existing_variants:
            try:
                attrs = json.loads(variant.selected_attributes)
                existing_keys.add(selected_attributes_to_key(attrs))
            except json.JSONDecodeError:
                continue

        # Generate all combinations with all selected options (old + new)
        combinations = await generate_variant_combinations(db, attribute_ids, product_id)

        # Filter to only new combinations (not already existing)
        new_combinations = []
        for combo in combinations:
            key = selected_attributes_to_key(combo["selected_attributes"])
            if key not in existing_keys:
                new_combinations.append(combo)

        # Create new variants
        new_variants_count = 0
        for combo in new_combinations:
            sku = build_sku(product.product_code, combo["selected_attributes"])

            # Check SKU doesn't already exist
            existing_sku = (
                db.query(ProductVariant).filter(ProductVariant.sku == sku).first()
            )
            if existing_sku:
                continue

            new_variant = ProductVariant(
                product_id=product_id,
                sku=sku,
                selected_attributes=json.dumps(combo["selected_attributes"]),
                 price=0,
                stock_quantity=0,
                is_active=True,
            )
            db.add(new_variant)
            new_variants_count += 1

        db.commit()

        total_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == product_id)
            .count()
        )

        logger.info(
            f"✅ New Variants Generated | "
            f"Product={product_id} | "
            f"New={new_variants_count} | "
            f"Total={total_variants} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": f"Generated {new_variants_count} new variants.",
            "product_id": product_id,
            "new_variants_count": new_variants_count,
            "total_variants_now": total_variants,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ New Variants Generation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate new variants.",
        )


@router.delete("/variants/{variant_id}", status_code=status.HTTP_200_OK)
async def delete_variant(
    db: db_dependency,
    admin: admin_dependency,
    variant_id: int = Path(gt=0),
):
    """
    Delete a variant.
    DELETE /admin/products/variants/{variant_id}
    """
    try:
        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found."
            )

        # Check if variant is used in any orders
        order_items = (
            db.query(OrderItem)
            .filter(OrderItem.selected_attributes == variant.selected_attributes)
            .filter(OrderItem.product_id == variant.product_id)
            .first()
        )

        if order_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete variant: it is used in existing orders.",
            )

        deleted_sku = variant.sku
        db.delete(variant)
        db.commit()

        logger.info(
            f"✅ Variant Deleted | "
            f"ID={variant_id} | "
            f"SKU={deleted_sku} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Variant deleted successfully.",
            "deleted_variant_id": variant_id,
            "deleted_sku": deleted_sku,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Variant Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete variant.",
        )