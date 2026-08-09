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
from app.models.attribute_option import AttributeOption
from app.models.attribute import Attribute
from app.schemas.cart import CartItemCreate, CartItemUpdate

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

        if not product.is_in_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name}' is out of stock.",
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
            # Update quantity instead of adding duplicate
            existing.quantity += item.quantity
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
    Calculate the total price for an item including selected attribute option prices.
    
    Args:
        db: Database session
        product_id: ID of the product
        selected_attributes: JSON string like {"Size": "XL", "Color": "Red"}
    
    Returns:
        Total unit price including attribute additions
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return 0
    
    total_price = float(product.base_price)
    
    # If attributes are selected, add their prices
    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            # Get all attribute options for this product
            product_attrs = (
                db.query(ProductAttributeOption)
                .filter(ProductAttributeOption.product_id == product_id)
                .all()
            )
            
            # Build a lookup for quick access
            attr_lookup = {}
            for pa in product_attrs:
                if pa.attribute_id not in attr_lookup:
                    attr_lookup[pa.attribute_id] = []
                attr_lookup[pa.attribute_id].append(pa.option_id)
            
            # Calculate additional price for each selected option
            for attr_id_str, option_value in attrs.items():
                try:
                    attr_id = int(attr_id_str)
                    if attr_id in attr_lookup:
                        option = db.query(AttributeOption).filter(
                            AttributeOption.id == option_value,
                            AttributeOption.attribute_id == attr_id
                        ).first()
                        if option and option.additional_price:
                            total_price += float(option.additional_price)
                except (ValueError, TypeError):
                    continue
                    
        except json.JSONDecodeError:
            pass  # Invalid JSON, ignore attribute pricing
    
    return total_price


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
                    "base_price": str(product.base_price),
                    "unit_price": str(unit_price),
                    "quantity": cart_item.quantity,
                    "subtotal": str(subtotal),
                    "selected_attributes": cart_item.selected_attributes,
                    "selected_attributes_display": selected_attrs_display,
                    "image_url": file.file_url if file else None,
                    "is_in_stock": product.is_in_stock,
                    "created_at": cart_item.created_at.isoformat(),
                }
            )

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
            "items": items,
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