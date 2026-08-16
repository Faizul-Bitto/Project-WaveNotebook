import json
from itertools import product

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute_option import ProductAttributeOption
from app.models.product_variant import ProductVariant


async def generate_variant_combinations(
    db: Session,
    attribute_ids: list[int],
    product_id: int = None,
) -> list[dict]:
    """
    Generate all possible variant combinations from the selected attribute options.
    """
    attributes = db.query(Attribute).filter(Attribute.id.in_(attribute_ids)).all()
    if not attributes:
        return []

    attribute_options = []
    for attr in attributes:
        if product_id:
            selected_options = (
                db.query(ProductAttributeOption)
                .filter(
                    ProductAttributeOption.product_id == product_id,
                    ProductAttributeOption.attribute_id == attr.id,
                )
                .all()
            )
            option_ids = [so.option_id for so in selected_options]
            options = (
                db.query(AttributeOption)
                .filter(AttributeOption.id.in_(option_ids))
                .all()
            )
        else:
            options = (
                db.query(AttributeOption)
                .filter(AttributeOption.attribute_id == attr.id)
                .all()
            )

        if not options:
            continue

        attribute_options.append(
            {
                "attribute_id": attr.id,
                "attribute_name": attr.name,
                "options": options,
            }
        )

    if not attribute_options:
        return []

    option_lists = [ao["options"] for ao in attribute_options]
    combinations = list(product(*option_lists))

    result = []
    for combo in combinations:
        selected_attributes = {}
        for i, option in enumerate(combo):
            attr_name = attribute_options[i]["attribute_name"]
            selected_attributes[attr_name] = option.value

        result.append(
            {
                "selected_attributes": selected_attributes,
                "price": 0,
            }
        )

    return result


def build_sku(product_code: str, selected_attributes: dict) -> str:
    """
    Build a unique SKU for a variant.
    Format: {product_code}-{Value1}-{Value2}-{Value3}
    """
    values = [str(v).replace(" ", "-") for v in selected_attributes.values()]
    return f"{product_code}-{'-'.join(values)}"


def selected_attributes_to_key(selected_attributes: dict) -> str:
    """
    Convert selected attributes dict to a string key for matching.
    Example: {"Size": "A4", "Color": "Black"} -> "A4-Black"
    """
    values = [str(v) for v in selected_attributes.values()]
    return "-".join(values)


def find_matching_variant(db: Session, product_id: int, selected_attributes: dict):
    """
    Find a variant that matches the given selected attributes.
    """
    from app.models.product_variant import ProductVariant

    variants = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.is_active == True,
        )
        .all()
    )

    for variant in variants:
        try:
            variant_attrs = json.loads(variant.selected_attributes)
        except json.JSONDecodeError:
            continue

        if variant_attrs == selected_attributes:
            return variant

    return None


def compute_product_in_stock(db: Session, product_id: int) -> bool:
    """
    Compute whether a product is in stock based on its variants.
    Returns True if any active variant has stock_quantity > 0.
    """
    from app.models.product_variant import ProductVariant

    in_stock_variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.product_id == product_id,
            ProductVariant.is_active == True,
            ProductVariant.stock_quantity > 0,
        )
        .first()
    )
    return in_stock_variant is not None


def get_variant_for_order(db: Session, product_id: int, selected_attributes: str = None):
    """
    Find the specific ProductVariant for a product based on selected attribute
    selections. The selected_attributes parameter is a JSON string in
    {attr_id: option_id} format (as used by cart items / order items).

    Returns the matching variant or None if no variant is found.
    """
    selected_attrs = {}
    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            selected_attrs = resolve_attrs_display(db, attrs)
        except (json.JSONDecodeError, TypeError):
            selected_attrs = {}

    return find_matching_variant(db, product_id, selected_attrs)


def get_variant_stock(db: Session, product_id: int, selected_attributes: str = None) -> int:
    """
    Get the stock quantity of the specific variant for a product.
    Returns 0 if the variant is not found.
    """
    variant = get_variant_for_order(db, product_id, selected_attributes)
    if not variant:
        return 0
    return variant.stock_quantity


def validate_and_decrement_stock(db: Session, product_id: int, selected_attributes: str = None, quantity: int = 1) -> ProductVariant:
    """
    Atomically validate that sufficient stock exists and decrement it.

    Uses a conditional UPDATE (``WHERE stock_quantity >= quantity``) so that
    concurrent transactions cannot oversell — only one will succeed per unit of
    stock.

    Raises ValueError if the variant is not found, inactive, or has insufficient
    stock. Returns the refreshed variant on success.
    """
    variant = get_variant_for_order(db, product_id, selected_attributes)

    if not variant:
        raise ValueError("Variant not found for this product configuration.")

    if not variant.is_active:
        raise ValueError("Selected variant is not available.")

    stmt = (
        update(ProductVariant)
        .where(
            ProductVariant.id == variant.id,
            ProductVariant.stock_quantity >= quantity,
        )
        .values(stock_quantity=ProductVariant.stock_quantity - quantity)
    )
    result = db.execute(stmt)

    if result.rowcount == 0:
        db.refresh(variant)
        raise ValueError(
            f"Insufficient stock. Only {variant.stock_quantity} item(s) available, "
            f"but {quantity} requested."
        )

    db.refresh(variant)
    return variant


def restore_variant_stock(db: Session, product_id: int, selected_attributes: str = None, quantity: int = 1) -> None:
    """
    Increment variant stock back (used when an order is cancelled, returned,
    or its items are modified/removed).
    """
    variant = get_variant_for_order(db, product_id, selected_attributes)
    if variant:
        variant.stock_quantity += quantity
        db.add(variant)



def build_attributes_display(db, selected_attributes: str = None):
    """
    Build a human-readable string of selected attributes.
    Example: "Size: XL, Color: Red"
    """
    import json
    from app.models.attribute import Attribute
    from app.models.attribute_option import AttributeOption

    if not selected_attributes:
        return None
    try:
        attrs = json.loads(selected_attributes)
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
        return ", ".join(display_parts) if display_parts else None
    except json.JSONDecodeError:
        return None


def resolve_attrs_display(db, attrs) -> dict:
    """
    Convert {attr_id: option_id} format to {attr_name: option_value} format.
    Accepts a dict of {str(attr_id): option_id}.
    """
    from app.models.attribute import Attribute
    from app.models.attribute_option import AttributeOption

    if not attrs or not isinstance(attrs, dict):
        return {}
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
    return selected_attrs