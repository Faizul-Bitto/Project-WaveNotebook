import json

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption


def build_user_snapshot(db: Session, user_id: int, full_name: str, phone_number: str) -> str:
    """
    Build a JSON snapshot of user info at the time of ordering.
    This survives user deletion so order history is always preserved.
    """
    user = db.query(User).filter(User.id == user_id).first() if user_id else None
    snapshot = {
        "user_id": user_id,
        "full_name": full_name,
        "phone_number": phone_number,
        "email": user.email if user else None,
    }
    return json.dumps(snapshot)


def build_product_snapshot(db: Session, product_id: int) -> str:
    """
    Build a JSON snapshot of product info at the time of ordering.
    This survives product deletion so orders always show what was bought.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return json.dumps({"product_id": product_id})

    snapshot = {
        "product_id": product.id,
        "product_code": product.product_code,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
    }
    return json.dumps(snapshot)


def build_variant_snapshot(db: Session, product_id: int, selected_attributes: str = None) -> str:
    """
    Build a JSON snapshot of variant options and price at the time of ordering.
    Resolves {attr_id: option_id} into {attr_name: option_value} for display.
    Survives variant deletion so order always shows exact options and price paid.
    """
    from app.utils.variant_generator import find_matching_variant, resolve_attrs_display

    snapshot = {
        "selected_attributes_display": None,
        "selected_attributes_raw": selected_attributes,
        "price": None,
        "sku": None,
    }

    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            display = resolve_attrs_display(db, attrs)
            if display:
                snapshot["selected_attributes_display"] = ", ".join(
                    f"{k}: {v}" for k, v in display.items()
                )
                variant = find_matching_variant(db, product_id, display)
                if variant:
                    snapshot["price"] = str(variant.price) if variant.price is not None else None
                    snapshot["sku"] = variant.sku
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return json.dumps(snapshot)


def parse_snapshot(snapshot_str: str) -> dict:
    """Safely parse a snapshot JSON string into a dict."""
    try:
        return json.loads(snapshot_str) if snapshot_str else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def serialize_order_item(db: Session, item) -> dict:
    """
    Serialize an OrderItem for API response, falling back to snapshots
    when the related product/variant has been deleted.
    """
    from app.utils.variant_generator import build_attributes_display

    product_snap = parse_snapshot(item.product_snapshot)
    variant_snap = parse_snapshot(item.variant_snapshot)

    # Try live product first, fall back to snapshot
    product = None
    if item.product_id is not None:
        product = db.query(Product).filter(Product.id == item.product_id).first()

    product_name = None
    if product:
        product_name = product.name
    elif product_snap.get("name"):
        product_name = product_snap["name"]
    else:
        product_name = f"Product #{item.product_id or '(deleted)'}"

    product_code = None
    if product:
        product_code = product.product_code
    elif product_snap.get("product_code"):
        product_code = product_snap["product_code"]

    # Selected attributes display: prefer snapshot, then live query
    selected_attrs_display = None
    if variant_snap.get("selected_attributes_display"):
        selected_attrs_display = variant_snap["selected_attributes_display"]
    else:
        selected_attrs_display = build_attributes_display(db, item.selected_attributes)

    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": product_name,
        "product_code": product_code,
        "quantity": item.quantity,
        "unit_price": str(item.unit_price),
        "price_at_purchase": str(item.price_at_purchase),
        "selected_attributes": item.selected_attributes,
        "selected_attributes_display": selected_attrs_display,
        "product_snapshot": product_snap,
        "variant_snapshot": variant_snap,
    }
