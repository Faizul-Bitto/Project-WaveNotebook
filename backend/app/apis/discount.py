import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.discount import Discount
from app.models.discount_scope import DiscountScope
from app.models.bundle_rule import BundleRule
from app.models.bundle_slab import BundleSlab
from app.models.bogo_rule import BogoRule
from app.models.product import Product
from app.models.category import Category
from app.services.discount_service import (
    is_discount_valid,
    get_product_discount_info,
    calculate_cart_discounts,
)

router = APIRouter(
    prefix="/discounts",
    tags=["Discounts"],
)


@router.get("/offers", status_code=status.HTTP_200_OK)
async def get_active_offers(
    db: db_dependency,
    type: str = Query(None, alias="discount_type"),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all active discount/bundle/BOGO offers for the customer-facing Offers page.
    GET /discounts/offers
    """
    try:
        from datetime import datetime
        now = datetime.now()

        query = (
            db.query(Discount)
            .filter(
                Discount.status == "active",
                Discount.start_date <= now,
                or_(Discount.end_date.is_(None), Discount.end_date > now),
            )
        )

        if type:
            query = query.filter(Discount.type == type)

        discounts = query.order_by(Discount.start_date.desc()).offset(skip).limit(limit).all()
        total = query.order_by(None).count()

        result = []
        for discount in discounts:
            offer = {
                "id": discount.id,
                "name": discount.name,
                "type": discount.type,
                "value_type": discount.value_type,
                "value": str(discount.value) if discount.value is not None else None,
                "max_discount_cap": str(discount.max_discount_cap) if discount.max_discount_cap is not None else None,
                "free_shipping": discount.free_shipping,
                "start_date": discount.start_date.isoformat() if discount.start_date else None,
                "end_date": discount.end_date.isoformat() if discount.end_date else None,
                "scopes": [],
                "bundle_rule": None,
                "bogo_rule": None,
                "badge_text": None,
                "badge_type": None,
            }

            # Scopes
            scopes = db.query(DiscountScope).filter(DiscountScope.discount_id == discount.id).all()
            offer["scopes"] = [
                {
                    "scope_type": s.scope_type,
                    "scope_id": s.scope_id,
                    "scope_name": _get_scope_name(db, s.scope_type, s.scope_id),
                }
                for s in scopes
            ]

            # Bundle rule
            br = db.query(BundleRule).filter(BundleRule.discount_id == discount.id).first()
            if br:
                bundle_data = {
                    "id": br.id,
                    "bundle_type": br.bundle_type,
                    "free_shipping": br.free_shipping,
                    "required_products": [],
                    "slabs": [],
                }

                if br.required_products:
                    try:
                        req_ids = json.loads(br.required_products)
                        bundle_data["required_products"] = [
                            {"id": pid, "name": p.name, "slug": p.slug}
                            for pid in req_ids
                            if (p := db.query(Product).filter(Product.id == pid).first())
                        ]
                    except (json.JSONDecodeError, TypeError):
                        pass

                if br.bundle_type == "quantity":
                    slabs = db.query(BundleSlab).filter(
                        BundleSlab.bundle_rule_id == br.id
                    ).order_by(BundleSlab.min_quantity).all()
                    bundle_data["slabs"] = [
                        {
                            "min_quantity": s.min_quantity,
                            "value_type": s.value_type,
                            "value": str(s.value),
                        }
                        for s in slabs
                    ]

                offer["bundle_rule"] = bundle_data

            # BOGO rule
            bogo = db.query(BogoRule).filter(BogoRule.discount_id == discount.id).first()
            if bogo:
                product = db.query(Product).filter(Product.id == bogo.product_id).first()
                offer["bogo_rule"] = {
                    "id": bogo.id,
                    "product_id": bogo.product_id,
                    "product_name": product.name if product else None,
                    "product_slug": product.slug if product else None,
                    "buy_quantity": bogo.buy_quantity,
                    "get_quantity": bogo.get_quantity,
                    "get_discount_percent": str(bogo.get_discount_percent),
                }

            # Build badge text
            if discount.type == "percentage":
                offer["badge_text"] = f"{int(float(discount.value))}% OFF"
                offer["badge_type"] = "discount"
            elif discount.type == "flat":
                offer["badge_text"] = f"৳{float(discount.value):.0f} OFF"
                offer["badge_type"] = "discount"
            elif discount.type == "bundle" and br:
                if br.bundle_type == "quantity":
                    slabs = db.query(BundleSlab).filter(BundleSlab.bundle_rule_id == br.id).order_by(BundleSlab.min_quantity).all()
                    if slabs:
                        s = slabs[0]
                        if s.value_type == "percentage":
                            offer["badge_text"] = f"{s.min_quantity}টি কিনলে {int(float(s.value))}% ছাড়"
                        else:
                            offer["badge_text"] = f"{s.min_quantity}টি কিনলে ৳{float(s.value):.0f} ছাড়"
                        offer["badge_type"] = "discount"
                elif br.bundle_type == "combo":
                    offer["badge_text"] = "কম্বিন অফার"
                    offer["badge_type"] = "discount"
            elif discount.type == "bogo" and bogo:
                offer["badge_text"] = f"{bogo.buy_quantity}+{bogo.get_quantity} FREE"
                offer["badge_type"] = "bogo"
            elif discount.type == "free_shipping":
                offer["badge_text"] = "ফ্রি শিপিং"
                offer["badge_type"] = "free_shipping"

            result.append(offer)

        logger.info(f"🎁 Offers Retrieved | Count={len(result)}")

        return {
            "message": "Active offers retrieved successfully.",
            "total": total,
            "offers": result,
        }

    except Exception as e:
        logger.error(f"❌ Error retrieving offers | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve offers.",
        )


@router.get("/product/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_discounts(
    db: db_dependency,
    product_id: int,
    unit_price: float = Query(None, description="Unit price to calculate discount against (e.g. a selected variant price)."),
):
    """
    Get discount information for a specific product.
    GET /discounts/product/{id}
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        info = get_product_discount_info(db, product_id, unit_price=unit_price)

        return {
            "message": "Product discount info retrieved.",
            "product_id": product_id,
            "product_name": product.name,
            "discount_info": info,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving product discounts | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product discounts.",
        )


@router.post("/calculate-cart", status_code=status.HTTP_200_OK)
async def calculate_cart(
    db: db_dependency,
    payload: dict = None,
):
    """
    Calculate discounts for a cart (preview).
    POST /discounts/calculate-cart
    Body: {"cart_items": [{"product_id": 1, "quantity": 2, "selected_attributes": "...", "unit_price": 100}]}
    """
    try:
        if not payload or "cart_items" not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cart_items is required.",
            )

        cart_items = payload["cart_items"]
        result = calculate_cart_discounts(db, cart_items)

        return {
            "message": "Cart discount calculation complete.",
            "calculation": result,
        }

    except Exception as e:
        logger.error(f"❌ Error calculating cart discounts | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate cart discounts.",
        )


def _get_scope_name(db, scope_type: str, scope_id: int) -> str | None:
    """Get the human-readable name for a scope."""
    try:
        if scope_type == "product":
            product = db.query(Product).filter(Product.id == scope_id).first()
            return product.name if product else None
        elif scope_type == "category":
            category = db.query(Category).filter(Category.id == scope_id).first()
            return category.name if category else None
    except Exception:
        pass
    return None
