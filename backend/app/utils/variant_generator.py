import json
from itertools import product

from sqlalchemy.orm import Session

from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute_option import ProductAttributeOption


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