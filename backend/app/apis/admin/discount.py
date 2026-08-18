import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Query, Body
from sqlalchemy import or_
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.discount import Discount
from app.models.discount_scope import DiscountScope
from app.models.bundle_rule import BundleRule
from app.models.bundle_slab import BundleSlab
from app.models.bogo_rule import BogoRule
from app.models.discount_usage import DiscountUsage
from app.models.product import Product
from app.models.category import Category
from app.models.spend_based_rule import SpendBasedRule
from app.models.spend_based_slab import SpendBasedSlab
from app.schemas.discount import DiscountCreate, DiscountUpdate

router = APIRouter(
    prefix="/admin/discounts",
    tags=["Admin - Discounts"],
)


DISCOUNT_TYPES = ["percentage", "flat", "bundle", "bogo", "free_shipping", "spend_based"]
DISCOUNT_STATUSES = ["active", "inactive"]


def validate_discount_data(data, is_update: bool = False):
    """Validate discount payload common fields."""
    if not is_update:
        if not data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount name is required.",
            )
        if data.type not in DISCOUNT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type. Must be one of: {', '.join(DISCOUNT_TYPES)}",
            )

    if data.value_type and data.value_type not in ("percentage", "flat"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="value_type must be 'percentage' or 'flat'.",
        )

    if data.value_type == "percentage" and data.value is not None:
        if data.value < 0 or data.value > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Percentage value must be between 0 and 100.",
            )

    if data.start_date and data.end_date and data.end_date <= data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date.",
        )

    if data.scope_type and data.scope_type not in ("product", "category"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scope_type must be 'product' or 'category'.",
        )

    if data.bundle_type and data.bundle_type not in ("quantity", "combo"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bundle_type must be 'quantity' or 'combo'.",
        )

    if getattr(data, 'get_discount_percent', None) is not None:
        if data.get_discount_percent < 0 or data.get_discount_percent > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="get_discount_percent must be between 0 and 100.",
            )


def get_discount_detail(db, discount: Discount) -> dict:
    """Build a full detail dict for a discount including related data."""
    result = {
        "id": discount.id,
        "name": discount.name,
        "type": discount.type,
        "value_type": discount.value_type,
        "value": str(discount.value) if discount.value is not None else None,
        "max_discount_cap": str(discount.max_discount_cap) if discount.max_discount_cap is not None else None,
        "free_shipping": discount.free_shipping,
        "start_date": discount.start_date.isoformat() if discount.start_date else None,
        "end_date": discount.end_date.isoformat() if discount.end_date else None,
        "status": discount.status,
        "created_at": discount.created_at.isoformat(),
        "updated_at": discount.updated_at.isoformat(),
        "scopes": [],
        "bundle_rule": None,
        "bogo_rule": None,
        "spend_based_rule": None,
    }

    # Scopes
    scopes = db.query(DiscountScope).filter(DiscountScope.discount_id == discount.id).all()
    result["scopes"] = [
        {"scope_type": s.scope_type, "scope_id": s.scope_id} for s in scopes
    ]

    # Bundle rule
    br = db.query(BundleRule).filter(BundleRule.discount_id == discount.id).first()
    if br:
        bundle_data = {
            "id": br.id,
            "bundle_type": br.bundle_type,
            "required_products": json.loads(br.required_products) if br.required_products else [],
            "free_shipping": br.free_shipping,
            "slabs": [],
        }
        if br.bundle_type == "quantity":
            slabs = db.query(BundleSlab).filter(BundleSlab.bundle_rule_id == br.id).order_by(BundleSlab.min_quantity).all()
            bundle_data["slabs"] = [
                {
                    "id": s.id,
                    "min_quantity": s.min_quantity,
                    "value_type": s.value_type,
                    "value": str(s.value),
                }
                for s in slabs
            ]
        result["bundle_rule"] = bundle_data

    # BOGO rule
    bogo = db.query(BogoRule).filter(BogoRule.discount_id == discount.id).all()
    if bogo:
        result["bogo_rule"] = {
            "id": bogo[0].id,
            "product_id": bogo[0].product_id,
            "product_ids": [b.product_id for b in bogo],
            "buy_quantity": bogo[0].buy_quantity,
            "get_quantity": bogo[0].get_quantity,
            "get_discount_percent": str(bogo[0].get_discount_percent),
        }

    # Spend-based rule
    sbr = db.query(SpendBasedRule).filter(SpendBasedRule.discount_id == discount.id).first()
    if sbr:
        slabs = db.query(SpendBasedSlab).filter(SpendBasedSlab.spend_based_rule_id == sbr.id).order_by(SpendBasedSlab.min_spend_amount).all()
        result["spend_based_rule"] = {
            "id": sbr.id,
            "scope_type": sbr.scope_type,
            "scope_id": sbr.scope_id,
            "slabs": [
                {
                    "id": s.id,
                    "min_spend_amount": str(s.min_spend_amount),
                    "value_type": s.value_type,
                    "value": str(s.value),
                }
                for s in slabs
            ],
        }

    return result


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_discounts(
    db: db_dependency,
    admin: admin_dependency,
    type: str = Query(None, alias="discount_type"),
    status: str = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all discounts with optional filtering by type and status.
    GET /admin/discounts
    """
    try:
        query = db.query(Discount)

        if type:
            if type not in DISCOUNT_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid type. Must be one of: {', '.join(DISCOUNT_TYPES)}",
                )
            query = query.filter(Discount.type == type)

        if status:
            if status not in DISCOUNT_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {', '.join(DISCOUNT_STATUSES)}",
                )
            query = query.filter(Discount.status == status)

        discounts = query.order_by(Discount.created_at.desc()).offset(skip).limit(limit).all()
        total = query.order_by(None).count()

        logger.info(
            f"📋 Discounts Retrieved | "
            f"Count={len(discounts)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discounts retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "discounts": [get_discount_detail(db, d) for d in discounts],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving discounts | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve discounts.",
        )


@router.get("/{discount_id}", status_code=status.HTTP_200_OK)
async def get_discount(
    db: db_dependency,
    admin: admin_dependency,
    discount_id: int = Path(gt=0),
):
    """
    Get a single discount with full details.
    GET /admin/discounts/{id}
    """
    try:
        discount = db.query(Discount).filter(Discount.id == discount_id).first()

        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount not found.",
            )

        logger.info(
            f"📋 Discount Retrieved | "
            f"ID={discount.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount retrieved successfully.",
            "discount": get_discount_detail(db, discount),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving discount | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve discount.",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_discount(
    db: db_dependency,
    admin: admin_dependency,
    discount_data: DiscountCreate,
):
    """
    Create a new discount rule.
    Supports all types: percentage, flat, bundle (quantity/combo), bogo, free_shipping.
    POST /admin/discounts
    """
    try:
        validate_discount_data(discount_data, is_update=False)

        now = datetime.now()

        # Create the discount
        discount = Discount(
            name=discount_data.name,
            type=discount_data.type,
            value_type=discount_data.value_type,
            value=discount_data.value,
            max_discount_cap=discount_data.max_discount_cap,
            free_shipping=discount_data.free_shipping or False,
            start_date=discount_data.start_date,
            end_date=discount_data.end_date,
            status="active",
        )
        db.add(discount)
        db.flush()

        # Create scope(s) for percentage/flat/free_shipping
        if discount_data.type in ("percentage", "flat", "free_shipping"):
            scope_ids = getattr(discount_data, 'scope_ids', None)
            if scope_ids and len(scope_ids) > 0:
                for sid in scope_ids:
                    scope = DiscountScope(
                        discount_id=discount.id,
                        scope_type=discount_data.scope_type,
                        scope_id=sid,
                    )
                    db.add(scope)
            elif discount_data.scope_type and discount_data.scope_id is not None:
                scope = DiscountScope(
                    discount_id=discount.id,
                    scope_type=discount_data.scope_type,
                    scope_id=discount_data.scope_id,
                )
                db.add(scope)
            elif discount_data.type == "free_shipping" and not discount_data.scope_type:
                # free_shipping without specific scope applies to entire cart
                pass

        # Create bundle rule for bundle type
        if discount_data.type == "bundle":
            bundle_rule = BundleRule(
                discount_id=discount.id,
                bundle_type=discount_data.bundle_type,
                required_products=discount_data.required_products,
                free_shipping=discount_data.free_shipping or False,
            )
            db.add(bundle_rule)
            db.flush()

            if discount_data.bundle_type == "quantity" and discount_data.bundle_slabs:
                for slab_data in discount_data.bundle_slabs:
                    slab = BundleSlab(
                        bundle_rule_id=bundle_rule.id,
                        min_quantity=slab_data.min_quantity,
                        value_type=slab_data.value_type,
                        value=slab_data.value,
                    )
                    db.add(slab)

            # Create scope(s) for quantity bundle
            if discount_data.bundle_type == "quantity":
                scope_ids = getattr(discount_data, 'scope_ids', None)
                if scope_ids and len(scope_ids) > 0:
                    for sid in scope_ids:
                        scope = DiscountScope(
                            discount_id=discount.id,
                            scope_type=discount_data.scope_type,
                            scope_id=sid,
                        )
                        db.add(scope)

        # Create BOGO rule(s)
        if discount_data.type == "bogo" and discount_data.bogo:
            product_ids = discount_data.bogo.product_ids or [discount_data.bogo.product_id]
            for pid in product_ids:
                if not pid:
                    continue
                product = db.query(Product).filter(Product.id == pid).first()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product with ID {pid} does not exist.",
                    )
                bogo = BogoRule(
                    discount_id=discount.id,
                    product_id=pid,
                    buy_quantity=discount_data.bogo.buy_quantity,
                    get_quantity=discount_data.bogo.get_quantity,
                    get_discount_percent=discount_data.bogo.get_discount_percent,
                )
                db.add(bogo)

        # Create spend-based rule
        if discount_data.type == "spend_based" and discount_data.spend_based:
            sbr = SpendBasedRule(
                discount_id=discount.id,
                scope_type=discount_data.spend_based.scope_type or "storewide",
                scope_id=discount_data.spend_based.scope_id,
            )
            db.add(sbr)
            db.flush()

            if discount_data.spend_based.slabs:
                for slab_data in discount_data.spend_based.slabs:
                    slab = SpendBasedSlab(
                        spend_based_rule_id=sbr.id,
                        min_spend_amount=slab_data.min_spend_amount,
                        value_type=slab_data.value_type,
                        value=slab_data.value,
                    )
                    db.add(slab)

        db.commit()
        db.refresh(discount)

        logger.info(
            f"✅ Discount Created | "
            f"ID={discount.id} | "
            f"Name={discount.name} | "
            f"Type={discount.type} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount created successfully.",
            "discount": get_discount_detail(db, discount),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Discount Creation Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create discount.",
        )


@router.put("/{discount_id}", status_code=status.HTTP_200_OK)
async def update_discount(
    db: db_dependency,
    admin: admin_dependency,
    discount_id: int = Path(gt=0),
    discount_data: DiscountUpdate = None,
):
    """
    Update a discount rule.
    PUT /admin/discounts/{id}
    """
    try:
        discount = db.query(Discount).filter(Discount.id == discount_id).first()

        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount not found.",
            )

        validate_discount_data(discount_data, is_update=True)

        # Update discount fields
        if discount_data.name is not None:
            discount.name = discount_data.name
        if discount_data.type is not None:
            discount.type = discount_data.type
        if discount_data.value_type is not None:
            discount.value_type = discount_data.value_type
        if discount_data.value is not None:
            discount.value = discount_data.value
        if discount_data.max_discount_cap is not None:
            discount.max_discount_cap = discount_data.max_discount_cap
        if discount_data.free_shipping is not None:
            discount.free_shipping = discount_data.free_shipping
        if discount_data.start_date is not None:
            discount.start_date = discount_data.start_date
        if discount_data.end_date is not None:
            discount.end_date = discount_data.end_date
        if discount_data.status is not None:
            discount.status = discount_data.status

        # Update scope(s)
        if discount_data.scope_type is not None:
            scope_ids = getattr(discount_data, 'scope_ids', None)
            if scope_ids and len(scope_ids) > 0:
                # Delete old scopes and create new ones
                db.query(DiscountScope).filter(DiscountScope.discount_id == discount_id).delete()
                for sid in scope_ids:
                    scope = DiscountScope(
                        discount_id=discount_id,
                        scope_type=discount_data.scope_type,
                        scope_id=sid,
                    )
                    db.add(scope)
            elif discount_data.scope_id is not None:
                # Delete old scopes and create new
                db.query(DiscountScope).filter(DiscountScope.discount_id == discount_id).delete()
                scope = DiscountScope(
                    discount_id=discount_id,
                    scope_type=discount_data.scope_type,
                    scope_id=discount_data.scope_id,
                )
                db.add(scope)

        # Update bundle rule
        if discount_data.type == "bundle" and discount_data.bundle_type:
            br = db.query(BundleRule).filter(BundleRule.discount_id == discount_id).first()

            if not br:
                br = BundleRule(
                    discount_id=discount_id,
                    bundle_type=discount_data.bundle_type,
                )
                db.add(br)
                db.flush()

            br.bundle_type = discount_data.bundle_type
            br.required_products = discount_data.required_products
            br.free_shipping = discount_data.free_shipping or False

            if discount_data.bundle_type == "quantity":
                # Delete old slabs
                db.query(BundleSlab).filter(BundleSlab.bundle_rule_id == br.id).delete()
                # Create new slabs
                if discount_data.bundle_slabs:
                    for slab_data in discount_data.bundle_slabs:
                        slab = BundleSlab(
                            bundle_rule_id=br.id,
                            min_quantity=slab_data.min_quantity,
                            value_type=slab_data.value_type,
                            value=slab_data.value,
                        )
                        db.add(slab)

                # Update BOGO rule(s)
        if discount_data.type == "bogo":
            db.query(BogoRule).filter(BogoRule.discount_id == discount_id).delete()
            db.flush()

            if discount_data.bogo:
                product_ids = discount_data.bogo.product_ids or [discount_data.bogo.product_id]
                for pid in product_ids:
                    if not pid:
                        continue
                    product = db.query(Product).filter(Product.id == pid).first()
                    if not product:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Product with ID {pid} does not exist.",
                        )
                    bogo = BogoRule(
                        discount_id=discount_id,
                        product_id=pid,
                        buy_quantity=discount_data.bogo.buy_quantity,
                        get_quantity=discount_data.bogo.get_quantity,
                        get_discount_percent=discount_data.bogo.get_discount_percent,
                    )
                    db.add(bogo)

        # Update spend-based rule
        if discount_data.type == "spend_based" and discount_data.spend_based:
            sbr = db.query(SpendBasedRule).filter(SpendBasedRule.discount_id == discount_id).first()

            if not sbr:
                sbr = SpendBasedRule(
                    discount_id=discount_id,
                    scope_type=discount_data.spend_based.scope_type or "storewide",
                    scope_id=discount_data.spend_based.scope_id,
                )
                db.add(sbr)
                db.flush()
            else:
                sbr.scope_type = discount_data.spend_based.scope_type or "storewide"
                sbr.scope_id = discount_data.spend_based.scope_id

            # Delete old slabs and create new ones
            db.query(SpendBasedSlab).filter(SpendBasedSlab.spend_based_rule_id == sbr.id).delete()
            if discount_data.spend_based.slabs:
                for slab_data in discount_data.spend_based.slabs:
                    slab = SpendBasedSlab(
                        spend_based_rule_id=sbr.id,
                        min_spend_amount=slab_data.min_spend_amount,
                        value_type=slab_data.value_type,
                        value=slab_data.value,
                    )
                    db.add(slab)

        db.commit()
        db.refresh(discount)

        logger.info(
            f"✅ Discount Updated | "
            f"ID={discount.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount updated successfully.",
            "discount": get_discount_detail(db, discount),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Discount Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update discount.",
        )


@router.delete("/{discount_id}", status_code=status.HTTP_200_OK)
async def delete_discount(
    db: db_dependency,
    admin: admin_dependency,
    discount_id: int = Path(gt=0),
):
    """
    Delete a discount (cascades to scopes, bundle rules, bogo rules).
    DELETE /admin/discounts/{id}
    """
    try:
        discount = db.query(Discount).filter(Discount.id == discount_id).first()

        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount not found.",
            )

        discount_name = discount.name
        discount_type = discount.type

        db.delete(discount)
        db.commit()

        logger.info(
            f"✅ Discount Deleted | "
            f"ID={discount_id} | "
            f"Name={discount_name} | "
            f"Type={discount_type} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount deleted successfully.",
            "deleted_discount_id": discount_id,
            "deleted_discount_name": discount_name,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Discount Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete discount.",
        )


@router.patch("/{discount_id}/status", status_code=status.HTTP_200_OK)
async def toggle_discount_status(
    db: db_dependency,
    admin: admin_dependency,
    discount_id: int = Path(gt=0),
    status_data: dict = Body(...),
):
    """
    Toggle discount status (active/inactive).
    PATCH /admin/discounts/{id}/status
    Body: {"status": "active"} or {"status": "inactive"}
    """
    try:
        new_status = status_data.get("status")
        if new_status not in DISCOUNT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(DISCOUNT_STATUSES)}",
            )

        discount = db.query(Discount).filter(Discount.id == discount_id).first()

        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount not found.",
            )

        old_status = discount.status
        discount.status = new_status
        db.commit()
        db.refresh(discount)

        logger.info(
            f"✅ Discount Status Toggled | "
            f"ID={discount.id} | "
            f"Status: {old_status} -> {discount.status} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount status updated successfully.",
            "discount_id": discount.id,
            "name": discount.name,
            "old_status": old_status,
            "new_status": discount.status,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Discount Status Toggle Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update discount status.",
        )


@router.get("/{discount_id}/usage", status_code=status.HTTP_200_OK)
async def get_discount_usage(
    db: db_dependency,
    admin: admin_dependency,
    discount_id: int = Path(gt=0),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get usage statistics for a discount.
    GET /admin/discounts/{id}/usage
    """
    try:
        discount = db.query(Discount).filter(Discount.id == discount_id).first()

        if not discount:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Discount not found.",
            )

        usages = (
            db.query(DiscountUsage)
            .filter(DiscountUsage.discount_id == discount_id)
            .order_by(DiscountUsage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        total = db.query(DiscountUsage).filter(
            DiscountUsage.discount_id == discount_id
        ).count()

        total_applied_amount = sum(float(u.applied_amount) for u in usages)

        logger.info(
            f"📊 Discount Usage Retrieved | "
            f"ID={discount.id} | "
            f"Count={len(usages)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Discount usage retrieved successfully.",
            "discount": {"id": discount.id, "name": discount.name, "type": discount.type},
            "total_uses": total,
            "total_applied_amount": str(round(total_applied_amount, 2)),
            "skip": skip,
            "limit": limit,
            "usages": [
                {
                    "id": u.id,
                    "order_id": u.order_id,
                    "applied_amount": str(u.applied_amount),
                    "created_at": u.created_at.isoformat(),
                }
                for u in usages
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving discount usage | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve discount usage.",
        )
