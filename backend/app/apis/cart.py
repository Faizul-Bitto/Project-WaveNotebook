import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.file import File
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_variant import ProductVariant
from app.schemas.cart import CartItemCreate, CartItemUpdate
from app.utils.variant_generator import find_matching_variant, compute_product_in_stock, get_variant_stock
from app.services.discount_service import calculate_cart_discounts, get_bogo_bonus_quantity

router = APIRouter(
    prefix="/cart",
    tags=["Cart"],
)


def get_or_create_cart_id() -> str:
    """
    Generate a new cart ID (client should store this).
    """
    return str(uuid.uuid4())


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    db: db_dependency,
    cart_session_id: str = Query(...),
    item: CartItemCreate = None,
):
    """
    Add item to cart.
    POST /cart?cart_session_id={cart_id}
    """
    try:
        # Validate product exists and is active
        product = db.query(Product).filter(
            Product.id == item.product_id, Product.is_active == True
        ).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

        available_stock = get_variant_stock(db, product.id, item.selected_attributes)
        if available_stock <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is out of stock.",
            )

        # BOGO adds free/discounted bonus units that also consume stock
        bonus_qty = get_bogo_bonus_quantity(db, product.id, item.quantity)
        total_needed = item.quantity + bonus_qty
        if available_stock < total_needed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available_stock} item(s) of '{product.name}' available in stock.",
            )

        # Validate that all product attributes have a selected option
        product_attrs = (
            db.query(ProductAttribute)
            .filter(ProductAttribute.product_id == item.product_id)
            .all()
        )
        if product_attrs:
            selected = {}
            if item.selected_attributes:
                try:
                    selected = json.loads(item.selected_attributes)
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid selected attributes format.",
                    )

            missing_attrs = []
            for pa in product_attrs:
                attr_id = str(pa.attribute_id)
                if attr_id not in selected or not selected[attr_id]:
                    attr = db.query(Attribute).filter(Attribute.id == pa.attribute_id).first()
                    missing_attrs.append(attr.name if attr else f"Attribute {pa.attribute_id}")

            if missing_attrs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Please select the following option(s): {', '.join(missing_attrs)}.",
                )

        # Check if same product + attributes already in cart
        existing = (
            db.query(CartItem)
            .filter(
                CartItem.cart_session_id == cart_session_id,
                CartItem.product_id == item.product_id,
                CartItem.selected_attributes == item.selected_attributes,
            )
            .first()
        )

        if existing:
            total_qty = existing.quantity + item.quantity
            total_bonus = get_bogo_bonus_quantity(db, product.id, total_qty)
            if total_qty + total_bonus > available_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_stock} item(s) of '{product.name}' available in stock.",
                )
            # Update quantity instead of adding duplicate
            existing.quantity = total_qty
            db.commit()
            db.refresh(existing)

            logger.info(
                f"✅ Cart Item Quantity Updated | "
                f"Cart={cart_session_id[:8]}... | "
                f"Product={item.product_id} | "
                f"Qty={existing.quantity}"
            )

            return {
                "message": "Cart item quantity updated.",
                "item": {
                    "id": existing.id,
                    "product_id": existing.product_id,
                    "quantity": existing.quantity,
                    "selected_attributes": existing.selected_attributes,
                    "available_stock": available_stock,
                },
            }

        # Add new cart item
        new_item = CartItem(
            cart_session_id=cart_session_id,
            product_id=item.product_id,
            quantity=item.quantity,
            selected_attributes=item.selected_attributes,
        )

        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        logger.info(
            f"✅ Cart Item Added | "
            f"Cart={cart_session_id[:8]}... | "
            f"Product={item.product_id} | "
            f"Qty={item.quantity}"
        )

        return {
            "message": "Item added to cart.",
            "item": {
                "id": new_item.id,
                "product_id": new_item.product_id,
                "quantity": new_item.quantity,
                "selected_attributes": new_item.selected_attributes,
                "available_stock": available_stock,
                "created_at": new_item.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Add to Cart Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart.",
        )


def calculate_item_price(db, product_id: int, selected_attributes: str = None) -> float:
    """
    Calculate the total price for an item using the variant system.
    
    Args:
        db: Database session
        product_id: ID of the product
        selected_attributes: JSON string like {"1": 5, "2": 8} (attribute_id: option_id)
    
    Returns:
        Total unit price from the matching variant
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return 0
    
    # If attributes are selected, find the matching variant
    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            
            # Convert attribute_id: option_id format to attribute_name: option_value format
            selected_attrs = {}
            for attr_id_str, option_id in attrs.items():
                try:
                    attr_id = int(attr_id_str)
                    attr = db.query(Attribute).filter(Attribute.id == attr_id).first()
                    option = db.query(AttributeOption).filter(
                        AttributeOption.id == option_id,
                        AttributeOption.attribute_id == attr_id
                    ).first()
                    if attr and option:
                        selected_attrs[attr.name] = option.value
                except (ValueError, TypeError):
                    continue
            
            if selected_attrs:
                variant = find_matching_variant(db, product_id, selected_attrs)
                if variant and variant.price is not None:
                    return float(variant.price)
        except json.JSONDecodeError:
            pass

    # If no variant found, check if there's a single variant for this product
    variant = (
        db.query(ProductVariant)
        .filter(ProductVariant.product_id == product_id)
        .first()
    )
    if variant and variant.price is not None:
        return float(variant.price)

    return 0


@router.get("", status_code=status.HTTP_200_OK)
async def get_cart(
    db: db_dependency,
    cart_session_id: str = Query(...),
):
    """
    Get cart items with full product details.
    GET /cart?cart_session_id={cart_id}
    """
    try:
        cart_items = (
            db.query(CartItem)
            .filter(CartItem.cart_session_id == cart_session_id)
            .order_by(CartItem.created_at.desc())
            .all()
        )

        items = []
        total_price = 0

        for cart_item in cart_items:
            product = db.query(Product).filter(Product.id == cart_item.product_id).first()

            if not product:
                continue

            # Get first file image
            file = (
                db.query(File).filter(File.product_id == product.id).first()
            )

            # Calculate unit price including selected attributes
            unit_price = calculate_item_price(db, cart_item.product_id, cart_item.selected_attributes)
            subtotal = unit_price * cart_item.quantity
            total_price += subtotal

            # Build human-readable selected attributes display
            selected_attrs_display = None
            if cart_item.selected_attributes:
                try:
                    attrs = json.loads(cart_item.selected_attributes)
                    display_parts = []
                    for attr_id_str, option_id in attrs.items():
                        try:
                            attr_id = int(attr_id_str)
                            option = db.query(AttributeOption).filter(
                                AttributeOption.id == option_id,
                                AttributeOption.attribute_id == attr_id
                            ).first()
                            if option:
                                attr = db.query(Attribute).filter(Attribute.id == attr_id).first()
                                attr_name = attr.name if attr else f"Attribute {attr_id}"
                                display_parts.append(f"{attr_name}: {option.value}")
                        except (ValueError, TypeError):
                            continue
                    if display_parts:
                        selected_attrs_display = ", ".join(display_parts)
                except json.JSONDecodeError:
                    pass

            items.append(
                {
                    "id": cart_item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "slug": product.slug,
                    "unit_price": str(unit_price),
                    "quantity": cart_item.quantity,
                    "subtotal": str(subtotal),
                    "selected_attributes": cart_item.selected_attributes,
                    "selected_attributes_display": selected_attrs_display,
                    "image_url": file.file_url if file else None,
                     "is_in_stock": compute_product_in_stock(db, product.id),
                     "available_stock": get_variant_stock(db, product.id, cart_item.selected_attributes),
                     "created_at": cart_item.created_at.isoformat(),
                }
            )

        # Calculate discounts for the cart
        cart_items_for_calc = [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "selected_attributes": item["selected_attributes"],
                "unit_price": float(item["unit_price"]),
            }
            for item in items
        ]

        discount_result = calculate_cart_discounts(db, cart_items_for_calc)

        # Merge per-item discount info
        for i, item in enumerate(items):
            calc_item = discount_result["items"][i]
            item["discount_amount"] = str(calc_item["discount_amount"])
            item["discounted_subtotal"] = str(calc_item["discounted_subtotal"])
            item["bonus_quantity"] = calc_item.get("bonus_quantity", 0)
            item["winning_rule"] = calc_item.get("winning_rule")
            item["simple_bogo"] = calc_item.get("simple_bogo", False)
            # Attach BOGO label info for display only when this specific item
            # actually received a bonus. Otherwise every variant of the same
            # product would incorrectly inherit the BOGO badge.
            if calc_item.get("bonus_quantity", 0) > 0:
                bogo_detail = next(
                    (b for b in discount_result.get("bogo_details", [])
                     if b["product_id"] == item["product_id"]),
                    None,
                )
                if bogo_detail:
                    item["bogo_bonus_quantity"] = bogo_detail["bonus_quantity"]
                    item["bogo_get_discount_percent"] = bogo_detail["get_discount_percent"]

        # display_subtotal: for simple 100% BOGO this is the actual charged amount,
        # otherwise it's the same as subtotal_before_discount.
        total_price = discount_result.get("display_subtotal", discount_result["subtotal_before_discount"])

        logger.info(
            f"🛒 Cart Retrieved | "
            f"Cart={cart_session_id[:8]}... | "
            f"Items={len(items)} | "
            f"Total={total_price}"
        )

        return {
            "message": "Cart retrieved successfully.",
            "cart_session_id": cart_session_id,
            "total_items": len(items),
            "total_price": str(total_price),
            "total_discount": str(discount_result["total_discount"]),
            "total_after_discount": str(discount_result["total_after_discount"]),
            "discount_breakdown": discount_result["discount_breakdown"],
            "bogo_details": discount_result.get("bogo_details", []),
            # Partial (<100%) BOGO offers awaiting customer consent.
            "pending_bogo_offers": discount_result.get("pending_bogo_offers", []),
            "free_shipping": discount_result["free_shipping"],
            "winning_rule": discount_result.get("winning_rule"),
            "items": items,
            "simple_bogo": discount_result.get("simple_bogo", False),
            "bogo_free_note": discount_result.get("bogo_free_note"),
        }

    except Exception as e:
        logger.error(f"❌ Get Cart Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart.",
        )


@router.put("/{item_id}", status_code=status.HTTP_200_OK)
async def update_cart_item(
    db: db_dependency,
    cart_session_id: str = Query(...),
    item_id: int = Path(gt=0),
    item_data: CartItemUpdate = None,
):
    """
    Update cart item quantity or attributes.
    PUT /cart/{item_id}?cart_session_id={cart_id}
    """
    try:
        cart_item = (
            db.query(CartItem)
            .filter(
                CartItem.id == item_id,
                CartItem.cart_session_id == cart_session_id,
            )
            .first()
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found."
            )

        if item_data.quantity is not None:
            if item_data.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0.",
                )

            selected_attrs = item_data.selected_attributes if item_data.selected_attributes is not None else cart_item.selected_attributes

            available_stock = get_variant_stock(db, cart_item.product_id, selected_attrs)
            # BOGO adds free/discounted bonus units that also consume stock
            bonus_qty = get_bogo_bonus_quantity(db, cart_item.product_id, item_data.quantity)
            if item_data.quantity + bonus_qty > available_stock:
                product = db.query(Product).filter(Product.id == cart_item.product_id).first()
                product_name = product.name if product else f"Product #{cart_item.product_id}"
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_stock} item(s) of '{product_name}' available in stock.",
                )

            cart_item.quantity = item_data.quantity

        if item_data.selected_attributes is not None:
            cart_item.selected_attributes = item_data.selected_attributes

        db.commit()
        db.refresh(cart_item)

        logger.info(
            f"✅ Cart Item Updated | "
            f"Cart={cart_session_id[:8]}... | "
            f"Item={item_id} | "
            f"Qty={cart_item.quantity}"
        )

        return {
            "message": "Cart item updated successfully.",
            "item": {
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "quantity": cart_item.quantity,
                "selected_attributes": cart_item.selected_attributes,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Cart Update Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item.",
        )


@router.delete("/{item_id}", status_code=status.HTTP_200_OK)
async def delete_cart_item(
    db: db_dependency,
    cart_session_id: str = Query(...),
    item_id: int = Path(gt=0),
):
    """
    Delete cart item.
    DELETE /cart/{item_id}?cart_session_id={cart_id}
    """
    try:
        cart_item = (
            db.query(CartItem)
            .filter(
                CartItem.id == item_id,
                CartItem.cart_session_id == cart_session_id,
            )
            .first()
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found."
            )

        product_id = cart_item.product_id

        db.delete(cart_item)
        db.commit()

        logger.info(
            f"✅ Cart Item Deleted | "
            f"Cart={cart_session_id[:8]}... | "
            f"Item={item_id} | "
            f"Product={product_id}"
        )

        return {
            "message": "Cart item deleted successfully.",
            "deleted_item_id": item_id,
            "deleted_product_id": product_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Cart Delete Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cart item.",
        )


@router.delete("", status_code=status.HTTP_200_OK)
async def clear_cart(
    db: db_dependency,
    cart_session_id: str = Query(...),
):
    """
    Clear all items from cart.
    DELETE /cart?cart_session_id={cart_id}
    """
    try:
        deleted = (
            db.query(CartItem)
            .filter(CartItem.cart_session_id == cart_session_id)
            .delete()
        )
        db.commit()

        logger.info(
            f"✅ Cart Cleared | "
            f"Cart={cart_session_id[:8]}... | "
            f"Deleted={deleted}"
        )

        return {
            "message": "Cart cleared successfully.",
            "deleted_items": deleted,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Cart Clear Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart.",
        )