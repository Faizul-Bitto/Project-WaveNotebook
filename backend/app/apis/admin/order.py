import json
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Path, Query, Response
from sqlalchemy import or_
from sqlalchemy import func, extract
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.attribute import Attribute
from app.models.attribute_option import AttributeOption
from app.models.product_attribute_option import ProductAttributeOption
from app.models.product_variant import ProductVariant
from app.models.order_adjustment import OrderAdjustment
from app.models.site_settings import SiteSettings
from app.schemas.order import OrderCreate, OrderStatusUpdate, OrderPreviewRequest
from app.schemas.order_adjustment import OrderAdjustmentCreate
from app.utils.variant_generator import (
    find_matching_variant,
    resolve_attrs_display,
    get_variant_stock,
    validate_and_decrement_stock,
    restore_variant_stock,
)
from app.utils.order_snapshots import (
    build_user_snapshot,
    build_product_snapshot,
    build_variant_snapshot,
    parse_snapshot,
    serialize_order_item,
)
from app.services.discount_service import (
    calculate_cart_discounts,
    record_discount_usage,
    get_bogo_bonus_quantity,
    compute_simple_bogo,
)
from app.services.export_service import build_csv, build_xlsx, export_response

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin - Orders"],
)


def calculate_unit_price(db, product_id: int, selected_attributes: str = None) -> float:
    """
    Calculate the unit price for an item using the variant system.
    Converts attr_id:option_id format to attr_name:option_value,
    then finds the matching ProductVariant.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return 0

    # If attributes are selected, find the matching variant
    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            selected_attrs = resolve_attrs_display(db, attrs)

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
async def get_all_orders(
    db: db_dependency,
    admin: admin_dependency,
    status_filter: str = Query(None, alias="status"),
    period: str = Query("all", pattern="^(all|year|month|day)$"),
    year: int = Query(None),
    month: int = Query(None),
    date_filter: str = Query(None, alias="date"),
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all orders (optional status filter).
    GET /admin/orders
    GET /admin/orders?status=pending
    GET /admin/orders?period=year&year=2026
    GET /admin/orders?period=month&year=2026&month=8
    GET /admin/orders?period=day&date=2026-08-28
    """
    try:
        query = db.query(Order)

        if status_filter:
            query = query.filter(Order.status == status_filter)

        if period == "year" and year:
            query = query.filter(extract("year", Order.created_at) == year)
        elif period == "month" and year and month:
            query = query.filter(
                extract("year", Order.created_at) == year,
                extract("month", Order.created_at) == month,
            )
        elif period == "day" and date_filter:
            try:
                day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )
            query = query.filter(
                Order.created_at >= day,
                Order.created_at < day + timedelta(days=1),
            )

        total = query.order_by(None).count()
        # Newest first — latest orders at the top of the admin list
        orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()

        logger.info(
            f"📦 Orders Retrieved | "
            f"Count={len(orders)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Orders retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "user_id": order.user_id,
                    "full_name": order.full_name,
                    "phone_number": order.phone_number,
                    "email": order.email,
                    "district": order.district,
                    "address": order.address,
                    "status": order.status,
                    "total_price": str(order.total_price),
                    "total_discount": str(order.total_discount),
                    "subtotal_before_discount": str(round(parse_snapshot(order.discount_snapshot).get("subtotal_before_discount", float(order.total_price) + float(order.total_discount)), 2)),
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                }
                for order in orders
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving orders | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders.",
        )


@router.get("/status-counts", status_code=status.HTTP_200_OK)
async def get_order_status_counts(
    db: db_dependency,
    admin: admin_dependency,
):
    """
    Get order counts grouped by all statuses plus total.
    GET /admin/orders/status-counts

    Used by the admin dashboard for real-time order status cards.
    """
    try:
        total = db.query(func.count(Order.id)).scalar() or 0

        status_counts = {}
        for status_value in [
            'pending', 'called', 'confirmed', 'processing',
            'shipped', 'delivered', 'cancelled', 'returned',
        ]:
            status_counts[status_value] = (
                db.query(func.count(Order.id)).filter(Order.status == status_value).scalar() or 0
            )

        logger.info(
            f"📊 Order status counts | "
            f"Total={total} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order status counts retrieved successfully.",
            "total": total,
            **status_counts,
        }
    except Exception as e:
        logger.error(
            f"❌ Error retrieving order status counts | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order status counts.",
        )


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_orders(
    db: db_dependency,
    admin: admin_dependency,
    type: str = Query(..., description="Search type: phone, name, address, or order_number"),
    value: str = Query(..., description="Search value"),
    skip: int = 0,
    limit: int = 20,
):
    """
    Search orders by phone, name, address, or order number.
    GET /admin/orders/search?type=all&value=anything  (searches all fields)
    GET /admin/orders/search?type=phone&value=01700000000
    GET /admin/orders/search?type=name&value=Rahim
    GET /admin/orders/search&type=address&value=Mirpur
    GET /admin/orders/search&type=order_number&value=ORD-20250809-7C0D2
    """
    try:
        valid_types = ["all", "phone", "name", "address", "order_number"]

        if type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search type. Must be one of: {', '.join(valid_types)}",
            )

        search_term = f"%{value}%"

        if type == "all":
            query = db.query(Order).filter(
                or_(
                    Order.order_number.contains(value),
                    Order.phone_number.contains(value),
                    Order.full_name.contains(value),
                    Order.address.contains(value),
                    Order.district.contains(value),
                )
            )
        elif type == "phone":
            query = db.query(Order).filter(Order.phone_number.contains(value))
        elif type == "name":
            query = db.query(Order).filter(Order.full_name.contains(value))
        elif type == "address":
            query = db.query(Order).filter(
                or_(
                    Order.address.contains(value),
                    Order.district.contains(value),
                )
            )
        elif type == "order_number":
            query = db.query(Order).filter(Order.order_number.contains(value))

        total = query.order_by(None).count()
        # Newest first — latest orders at the top of search results too
        orders = query.order_by(Order.id.desc()).offset(skip).limit(limit).all()

        logger.info(
            f"🔍 Orders Searched | Type={type} | Value={value} | Count={len(orders)} | Total={total} | Admin={admin.phone_number}"
        )

        return {
            "message": "Orders retrieved successfully.",
            "search_type": type,
            "search_value": value,
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "user_id": order.user_id,
                    "full_name": order.full_name,
                    "phone_number": order.phone_number,
                    "email": order.email,
                    "district": order.district,
                    "address": order.address,
                    "status": order.status,
                    "total_price": str(order.total_price),
                    "total_discount": str(order.total_discount),
                    "subtotal_before_discount": str(round(parse_snapshot(order.discount_snapshot).get("subtotal_before_discount", float(order.total_price) + float(order.total_discount)), 2)),
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                }
                for order in orders
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error searching orders | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search orders.",
        )


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_orders(
    db: db_dependency,
    admin: admin_dependency,
    status_filter: str = Query(None, alias="status"),
    period: str = Query("all", pattern="^(all|year|month|day)$"),
    year: int = Query(None),
    month: int = Query(None),
    date_filter: str = Query(None, alias="date"),
    search_type: str = Query(None, alias="search_type"),
    search_value: str = Query(None, alias="search_value"),
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    """
    Export orders (with all item details) to CSV or Excel.
    Respects the same filters as the list endpoint + active search.
    GET /admin/orders/export?format=csv
    GET /admin/orders/export?format=xlsx&period=month&year=2026&month=8
    """
    try:
        query = db.query(Order)

        if status_filter:
            query = query.filter(Order.status == status_filter)

        if period == "year" and year:
            query = query.filter(extract("year", Order.created_at) == year)
        elif period == "month" and year and month:
            query = query.filter(
                extract("year", Order.created_at) == year,
                extract("month", Order.created_at) == month,
            )
        elif period == "day" and date_filter:
            try:
                day = datetime.strptime(date_filter, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )
            query = query.filter(
                Order.created_at >= day,
                Order.created_at < day + timedelta(days=1),
            )

        if search_type and search_value:
            val = search_value
            if search_type == "all":
                query = query.filter(
                    or_(
                        Order.order_number.contains(val),
                        Order.phone_number.contains(val),
                        Order.full_name.contains(val),
                        Order.address.contains(val),
                        Order.district.contains(val),
                    )
                )
            elif search_type == "phone":
                query = query.filter(Order.phone_number.contains(val))
            elif search_type == "name":
                query = query.filter(Order.full_name.contains(val))
            elif search_type == "address":
                query = query.filter(
                    or_(Order.address.contains(val), Order.district.contains(val))
                )
            elif search_type == "order_number":
                query = query.filter(Order.order_number.contains(val))

        # Show orders in natural database order (ascending by id / oldest first)
        orders = query.order_by(Order.id.asc()).all()

        headers = [
            "Order ID",
            "Order Number",
            "Date",
            "Status",
            "Customer Name",
            "Phone",
            "Email",
            "District",
            "Thana",
            "Address",
            "Note",
            "Subtotal Before Discount",
            "Discount",
            "Total Price",
            "Free Shipping",
            "Items",
            "Discount Breakdown",
        ]

        rows = []
        for order in orders:
            snap = parse_snapshot(order.discount_snapshot)
            subtotal = float(
                snap.get(
                    "subtotal_before_discount",
                    float(order.total_price) + float(order.total_discount),
                )
            )
            items = (
                db.query(OrderItem)
                .filter(OrderItem.order_id == order.id)
                .order_by(OrderItem.id.asc())
                .all()
            )
            item_strs = []
            for it in items:
                ps = parse_snapshot(it.product_snapshot)
                vs = parse_snapshot(it.variant_snapshot)
                name = ps.get("name") or f"Product #{it.product_id}"
                attrs = vs.get("selected_attributes_display")
                qty = int(it.quantity or 0)
                bonus = int(it.bonus_quantity or 0)
                qty_str = str(qty) + (f" (+{bonus})" if bonus else "")
                parts = [name]
                if attrs:
                    parts.append(attrs)
                parts.append(f"Qty: {qty_str}")
                parts.append(f"Unit: {float(it.unit_price or 0):,.2f}")
                parts.append(f"Line Total: {float(it.price_at_purchase or 0):,.2f}")
                item_strs.append(" | ".join(parts))

            breakdown_strs = []
            for entry in snap.get("discount_breakdown", []):
                amount = float(entry.get("amount") or 0)
                if entry.get("type") == "bogo":
                    breakdown_strs.append(f"BOGO: {entry.get('name')} (FREE)")
                elif amount > 0:
                    breakdown_strs.append(f"{entry.get('name')} (-{amount:,.2f})")
            if snap.get("bogo_free_note"):
                breakdown_strs.append(snap["bogo_free_note"])

            rows.append(
                [
                    order.id,
                    order.order_number,
                    order.created_at.strftime("%Y-%m-%d %H:%M")
                    if order.created_at
                    else "",
                    order.status,
                    order.full_name,
                    order.phone_number,
                    order.email,
                    order.district,
                    order.thana,
                    order.address,
                    order.note,
                    round(subtotal, 2),
                    round(float(order.total_discount or 0), 2),
                    round(float(order.total_price or 0), 2),
                    snap.get("free_shipping", False),
                    "\n".join(item_strs),
                    "\n".join(breakdown_strs),
                ]
            )

        fmt = format.lower()
        if fmt == "csv":
            content = build_csv(headers, rows)
            filename = "orders.csv"
        else:
            content = build_xlsx(headers, rows, sheet_name="Orders")
            filename = "orders.xlsx"

        logger.info(
            f"📤 Orders Exported | Format={fmt.upper()} | "
            f"Count={len(rows)} | Admin={admin.phone_number}"
        )
        return export_response(content, filename, fmt)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error exporting orders | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export orders.",
        )


@router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_by_id(
    db: db_dependency, admin: admin_dependency, order_id: int = Path(gt=0)
):
    """
    Get single order with items and customer info.
    GET /admin/orders/{order_id}
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            logger.warning(
                f"⚠️ Order Not Found | "
                f"ID={order_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

        # Get user info
        user = db.query(User).filter(User.id == order.user_id).first()

        items_data = [serialize_order_item(db, item) for item in order_items]

        logger.info(
            f"📦 Order Retrieved | "
            f"ID={order.id} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order retrieved successfully.",
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "full_name": order.full_name,
                "phone_number": order.phone_number,
                "email": order.email,
                "district": order.district,
                "thana": order.thana or "",
                "note": order.note,
                "address": order.address,
                "status": order.status,
                    "total_price": str(order.total_price),
                    "total_discount": str(order.total_discount),
                    "subtotal_before_discount": str(round(parse_snapshot(order.discount_snapshot).get("subtotal_before_discount", float(order.total_price) + float(order.total_discount)), 2)),
                    "free_shipping": parse_snapshot(order.discount_snapshot).get("free_shipping", False),
                "discount_breakdown": parse_snapshot(order.discount_snapshot).get("discount_breakdown", []),
                "simple_bogo": parse_snapshot(order.discount_snapshot).get("simple_bogo", False),
                "bogo_free_note": parse_snapshot(order.discount_snapshot).get("bogo_free_note"),
                "bogo_details": parse_snapshot(order.discount_snapshot).get("bogo_details", []),
                "customer": {
                    "id": user.id if user else None,
                    "phone_number": user.phone_number if user else None,
                    "email": user.email if user else None,
                },
                "items": items_data,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving order | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to retrieve order.",
    )


@router.post("/calculate", status_code=status.HTTP_200_OK)
async def calculate_order_preview(
    db: db_dependency,
    admin: admin_dependency,
    payload: OrderPreviewRequest = None,
):
    """
    Calculate discounts/BOGO for a set of items without creating an order.
    Used by the admin order edit form to preview applicable discounts.
    POST /admin/orders/calculate
    """
    try:
        items = payload.items if payload and payload.items else []
        if not items:
            return {
                "message": "No items to calculate.",
                "subtotal_before_discount": 0.0,
                "total_discount": 0.0,
                "total_after_discount": 0.0,
                "items": [],
                "discount_breakdown": [],
                "free_shipping": False,
                "winning_rule": None,
                "bogo_details": [],
                "simple_bogo": False,
                "bogo_free_note": None,
            }

        order_items_data = []
        total_price = 0.0

        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total

            bonus_qty = get_bogo_bonus_quantity(db, item.product_id, item.quantity)
            order_items_data.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "selected_attributes": item.selected_attributes,
                    "unit_price": unit_price,
                }
            )

        cart_items_for_calc = [
            {
                "product_id": d["product_id"],
                "quantity": d["quantity"],
                "selected_attributes": d["selected_attributes"],
                "unit_price": d["unit_price"],
            }
            for d in order_items_data
        ]

        discount_result = calculate_cart_discounts(db, cart_items_for_calc)
        total_discount = discount_result["total_discount"]
        total_after_discount = discount_result["total_after_discount"]

        return {
            "message": "Discount preview calculated successfully.",
            "subtotal_before_discount": discount_result["subtotal_before_discount"],
            "total_discount": total_discount,
            "total_after_discount": total_after_discount,
            "items": discount_result["items"],
            "discount_breakdown": discount_result.get("discount_breakdown", []),
            "free_shipping": discount_result.get("free_shipping", False),
            "winning_rule": discount_result.get("winning_rule"),
            "bogo_details": discount_result.get("bogo_details", []),
            "simple_bogo": discount_result.get("simple_bogo", False),
            "bogo_free_note": discount_result.get("bogo_free_note"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Discount Preview Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate discount preview.",
        )


@router.put("/{order_id}", status_code=status.HTTP_200_OK)
async def update_order(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(gt=0),
    order_data: OrderCreate = None,
):
    """Update order customer info + items. Auto-creates user if phone doesn't exist."""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        if not order_data.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must have at least one item.")

        # Find or create user by phone number
        user = db.query(User).filter(User.phone_number == order_data.phone_number).first()
        if not user:
            user = User(phone_number=order_data.phone_number, email=order_data.email, role="customer", password=None)
            db.add(user)
            db.flush()
        elif order_data.email:
            user.email = order_data.email

        # Update order fields
        order.user_id = user.id
        order.full_name = order_data.full_name
        order.phone_number = order_data.phone_number
        order.email = order_data.email
        order.district = order_data.district
        order.thana = order_data.thana or ""
        order.note = order_data.note
        order.address = order_data.address
        order.user_snapshot = build_user_snapshot(
            db, user.id, order_data.full_name, order_data.phone_number, order_data.email
        )

        # Capture existing items BEFORE deleting so we can restore their stock
        old_items = (
            db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        )
        old_snapshot_map = {}
        for old_item in old_items:
            old_snapshot_map[old_item.product_id] = {
                "unit_price": float(old_item.unit_price),
                "product_snapshot": old_item.product_snapshot,
                "variant_snapshot": old_item.variant_snapshot,
                "selected_attributes": old_item.selected_attributes,
            }

        # Restore stock for old items (they were decremented when the order was created)
        for old_item in old_items:
            if old_item.product_id is not None:
                try:
                    restore_variant_stock(
                        db,
                        old_item.product_id,
                        old_item.selected_attributes,
                        old_item.quantity + (old_item.bonus_quantity or 0),
                    )
                    logger.info(
                        f"♻️ Stock Restored | Order={order_id} Product={old_item.product_id} "
                        f"Qty={old_item.quantity} Bonus={old_item.bonus_quantity}"
                    )
                except Exception as e:
                    logger.error(
                        f"⚠️ Failed to restore stock for order item | "
                        f"Order={order_id} Product={old_item.product_id} "
                        f"Qty={old_item.quantity} Bonus={old_item.bonus_quantity} Error={str(e)}"
                    )

        # Persist restored stock before proceeding so subsequent
        # validate_and_decrement_stock() raw SQL sees the updated values.
        db.flush()

        # Delete old items
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        # Create new items
        total_price = 0
        created_items = []

        for item in order_data.items:
            if item.product_id is None:
                # Product was deleted - keep original snapshot from existing order items
                fallback = old_snapshot_map.get(None)
                if not fallback:
                    for key, snap in old_snapshot_map.items():
                        if key is None:
                            fallback = snap
                            break

                if not fallback:
                    continue

                unit_price = fallback["unit_price"]
                line_total = unit_price * item.quantity
                total_price += line_total
                oi = OrderItem(
                    order_id=order_id, product_id=None, quantity=item.quantity,
                    unit_price=unit_price, price_at_purchase=line_total,
                    discount_amount=0,
                    selected_attributes=item.selected_attributes or fallback["selected_attributes"],
                    product_snapshot=fallback["product_snapshot"],
                    variant_snapshot=fallback["variant_snapshot"],
                )
                db.add(oi)
                created_items.append(oi)
                continue

            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {item.product_id} not found.")
            if not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is not available.")

            available_stock = get_variant_stock(db, item.product_id, item.selected_attributes)
            if available_stock <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is out of stock.")
            bonus_qty = get_bogo_bonus_quantity(db, item.product_id, item.quantity)
            total_needed = item.quantity + bonus_qty
            if available_stock < total_needed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_stock} item(s) of '{product.name}' available in stock.",
                )

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total
            oi = OrderItem(
                order_id=order_id, product_id=item.product_id, quantity=item.quantity,
                bonus_quantity=bonus_qty,
                unit_price=unit_price, price_at_purchase=line_total,
                discount_amount=0,
                selected_attributes=item.selected_attributes,
                product_snapshot=build_product_snapshot(db, item.product_id),
                variant_snapshot=build_variant_snapshot(db, item.product_id, item.selected_attributes)
            )
            db.add(oi)
            created_items.append(oi)

            try:
                validate_and_decrement_stock(
                    db,
                    item.product_id,
                    item.selected_attributes,
                    total_needed,
                )
            except ValueError as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

        # Calculate discounts using the shared discount service
        cart_items_for_calc = []
        for ci in created_items:
            cart_items_for_calc.append({
                "product_id": ci.product_id,
                "quantity": ci.quantity,
                "selected_attributes": ci.selected_attributes,
                "unit_price": float(ci.unit_price),
            })

        discount_result = calculate_cart_discounts(db, cart_items_for_calc)
        total_discount = discount_result["total_discount"]
        winning_rule = discount_result.get("winning_rule")

        # Map per-item discount amounts back to order items
        for i, calc_item in enumerate(discount_result["items"]):
            if i < len(created_items):
                created_items[i].discount_amount = calc_item["discount_amount"]
                created_items[i].price_at_purchase = calc_item["discounted_subtotal"]
                created_items[i].bonus_quantity = calc_item.get("bonus_quantity", 0)

        # Determine winning discount_id for usage tracking
        winning_discount_id = None
        if winning_rule and winning_rule.get("discount_id"):
            winning_discount_id = winning_rule["discount_id"]
        if discount_result.get("bogo_total", 0) > 0 and not winning_discount_id:
            for bd in discount_result.get("bogo_details", []):
                if bd.get("discount_id"):
                    winning_discount_id = bd["discount_id"]
                    break

        # Apply discount to total using the discount service's final amount.
        # Do NOT recompute from paid-only line totals and then subtract total_discount,
        # because that double-counts BOGO discounts.
        total_price = discount_result["total_after_discount"]
        order.total_price = round(total_price, 2)
        order.total_discount = total_discount
        order.discount_snapshot = json.dumps({
            "subtotal_before_discount": discount_result["subtotal_before_discount"],
            "total_discount": total_discount,
            "free_shipping": discount_result.get("free_shipping", False),
            "discount_breakdown": discount_result.get("discount_breakdown", []),
            "bogo_details": discount_result.get("bogo_details", []),
            "bogo_total": discount_result.get("bogo_total", 0),
            "winning_rule": winning_rule,
            "simple_bogo": discount_result.get("simple_bogo", False),
            "bogo_free_note": discount_result.get("bogo_free_note"),
        })

        # Record discount usage (tracks BOGO + price + spend-based separately)
        record_discount_usage(
            db,
            winning_discount_id,
            order_id,
            total_discount,
            discount_breakdown=discount_result.get("discount_breakdown", []) + discount_result.get("bogo_details", []),
        )

        db.commit()
        db.refresh(order)

        order_items = (
            db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        )

        logger.info(
            f"✅ Order Updated by Admin | "
            f"Order Number={order.order_number} | "
            f"Total={total_price} | "
            f"Discount={total_discount} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order updated successfully.",
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "full_name": order.full_name,
                "phone_number": order.phone_number,
                "email": order.email,
                "district": order.district,
                "thana": order.thana or "",
                "note": order.note,
                "address": order.address,
                "status": order.status,
                "total_price": str(order.total_price),
                "total_discount": str(order.total_discount),
                "subtotal_before_discount": str(round(discount_result["subtotal_before_discount"], 2)),
                "free_shipping": discount_result.get("free_shipping", False),
                "discount_breakdown": discount_result.get("discount_breakdown", []),
                "bogo_details": discount_result.get("bogo_details", []),
                "winning_rule": winning_rule,
                "simple_bogo": discount_result.get("simple_bogo", False),
                "bogo_free_note": discount_result.get("bogo_free_note"),
                "items": [
                    serialize_order_item(db, item) for item in order_items
                ],
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Order Update Failed | Error={str(e)} | Admin={admin.phone_number}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order.")


@router.put("/{order_id}/status", status_code=status.HTTP_200_OK)
async def update_order_status(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(gt=0),
    status_data: OrderStatusUpdate = None,
):
    """
    Update order status.
    PUT /admin/orders/{order_id}/status
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            logger.warning(
                f"⚠️ Order Not Found | "
                f"ID={order_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        valid_statuses = ["pending", "called", "confirmed", "processing", "shipped", "delivered", "cancelled", "returned"]

        if status_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        old_status = order.status
        new_status = status_data.status

        # Manage variant stock based on status transitions
        # Increment stock when transitioning to "returned" or "cancelled"
        # IMPORTANT: must restore quantity + bonus_quantity to fully return stock
        if new_status in ("returned", "cancelled") and old_status != new_status:
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            for item in order_items:
                try:
                    attrs = json.loads(item.selected_attributes) if item.selected_attributes else {}
                    variant = find_matching_variant(db, item.product_id, resolve_attrs_display(db, attrs))
                    if variant:
                        # Restore both paid and BOGO bonus units
                        total_restore = item.quantity + (item.bonus_quantity or 0)
                        variant.stock_quantity += total_restore
                        db.add(variant)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    continue

        order.status = new_status

        db.commit()
        db.refresh(order)

        logger.info(
            f"✅ Order Status Updated | "
            f"ID={order.id} | "
            f"Status: {old_status} -> {order.status} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order status updated successfully.",
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_price": str(order.total_price),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Order Status Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status.",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order_for_user(
    db: db_dependency,
    admin: admin_dependency,
    order_data: OrderCreate,
):
    """
    Admin creates order for a user (auto-creates user if phone doesn't exist).
    POST /admin/orders
    """
    try:
        if not order_data.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order must have at least one item.",
            )

        # Find or create user by phone number
        user = (
            db.query(User).filter(User.phone_number == order_data.phone_number).first()
        )

        if not user:
            user = User(
                phone_number=order_data.phone_number,
                email=order_data.email,
                role="customer",
                password=None,
            )
            db.add(user)
            db.flush()
            logger.info(
                f"✅ New User Auto-Created | User ID={user.id} | Phone={user.phone_number} | Admin={admin.phone_number}"
            )
        elif order_data.email:
            user.email = order_data.email

        # Generate unique order number
        from app.apis.order import generate_order_number

        order_number = generate_order_number()
        while db.query(Order).filter(Order.order_number == order_number).first():
            order_number = generate_order_number()

        # Calculate total price & validate products
        total_price = 0
        order_items_data = []

        for item in order_data.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product ID {item.product_id} not found.",
                )

            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is not available.",
                )

            available_stock = get_variant_stock(db, item.product_id, item.selected_attributes)
            if available_stock <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is out of stock.",
                )
            # BOGO adds free/discounted bonus units that also consume stock
            bonus_qty = get_bogo_bonus_quantity(db, item.product_id, item.quantity)
            total_needed = item.quantity + bonus_qty
            if available_stock < total_needed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only {available_stock} item(s) of '{product.name}' available in stock.",
                )

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total

            order_items_data.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "total_quantity": total_needed,
                    "bonus_quantity": bonus_qty,
                    "unit_price": unit_price,
                    "price_at_purchase": line_total,
                    "selected_attributes": item.selected_attributes,
                    "discount_amount": 0.0,
                }
            )

        # Calculate discounts using the shared discount service
        cart_items_for_calc = [
            {
                "product_id": d["product_id"],
                "quantity": d["quantity"],
                "selected_attributes": d["selected_attributes"],
                "unit_price": d["unit_price"],
            }
            for d in order_items_data
        ]

        discount_result = calculate_cart_discounts(db, cart_items_for_calc)
        total_discount = discount_result["total_discount"]
        winning_rule = discount_result.get("winning_rule")

        # Map per-item discount amounts back to order_items_data
        for i, calc_item in enumerate(discount_result["items"]):
            order_items_data[i]["discount_amount"] = calc_item["discount_amount"]
            order_items_data[i]["price_at_purchase"] = calc_item["discounted_subtotal"]
            order_items_data[i]["bonus_quantity"] = calc_item["bonus_quantity"]
            order_items_data[i]["total_quantity"] = calc_item["total_quantity"]

        # Apply discount to total (BOGO is reflected in item totals, not a discount line)
        total_price = round(discount_result["total_after_discount"], 2)

        # Determine winning discount_id for usage tracking
        winning_discount_id = None
        if winning_rule and winning_rule.get("discount_id"):
            winning_discount_id = winning_rule["discount_id"]
        if discount_result.get("bogo_details") and not winning_discount_id:
            for bd in discount_result.get("bogo_details", []):
                if bd.get("discount_id"):
                    winning_discount_id = bd["discount_id"]
                    break

        # Create order with user snapshot
        new_order = Order(
            order_number=order_number,
            user_id=user.id,
            full_name=order_data.full_name,
            phone_number=order_data.phone_number,
            email=order_data.email,
            district=order_data.district,
            thana=order_data.thana or "",
            note=order_data.note,
            address=order_data.address,
            status="pending",
            total_price=total_price,
            total_discount=total_discount,
            discount_snapshot=json.dumps({
                "subtotal_before_discount": discount_result["subtotal_before_discount"],
                "total_discount": total_discount,
                "free_shipping": discount_result.get("free_shipping", False),
                "discount_breakdown": discount_result.get("discount_breakdown", []),
                "bogo_details": discount_result.get("bogo_details", []),
                "bogo_total": discount_result.get("bogo_total", 0),
                "winning_rule": winning_rule,
                "simple_bogo": discount_result.get("simple_bogo", False),
                "bogo_free_note": discount_result.get("bogo_free_note"),
            }),
            user_snapshot=build_user_snapshot(
                db, user.id, order_data.full_name, order_data.phone_number, order_data.email
            ),
        )

        db.add(new_order)
        db.flush()

        # Create order items with product & variant snapshots
        for item_data in order_items_data:
            product_id = item_data["product_id"]
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=product_id,
                quantity=item_data["quantity"],
                bonus_quantity=item_data["bonus_quantity"],
                unit_price=item_data["unit_price"],
                price_at_purchase=item_data["price_at_purchase"],
                discount_amount=item_data["discount_amount"],
                selected_attributes=item_data["selected_attributes"],
                product_snapshot=build_product_snapshot(db, product_id),
                variant_snapshot=build_variant_snapshot(
                    db, product_id, item_data["selected_attributes"]
                ),
            )
            db.add(order_item)

            # Atomically validate and decrement variant stock (includes BOGO bonus units)
            try:
                validate_and_decrement_stock(
                    db,
                    item_data["product_id"],
                    item_data["selected_attributes"],
                    item_data["total_quantity"],
                )
            except ValueError as e:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

        # Record discount usage (tracks BOGO + A + spend-based separately)
        record_discount_usage(
            db,
            winning_discount_id,
            new_order.id,
            total_discount,
            discount_breakdown=discount_result.get("discount_breakdown", []) + discount_result.get("bogo_details", []),
        )

        db.commit()
        db.refresh(new_order)

        # Get order items for response
        order_items = (
            db.query(OrderItem).filter(OrderItem.order_id == new_order.id).all()
        )

        logger.info(
            f"✅ Order Created by Admin | "
            f"Order Number={new_order.order_number} | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number} | "
            f"Total={total_price} | "
            f"Discount={total_discount} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order created successfully.",
            "order": {
                "id": new_order.id,
                "order_number": new_order.order_number,
                "full_name": new_order.full_name,
                "phone_number": new_order.phone_number,
                "email": new_order.email,
                "district": new_order.district,
                "thana": new_order.thana or "",
                "note": new_order.note,
                "address": new_order.address,
                "status": new_order.status,
                "total_price": str(new_order.total_price),
                "total_discount": str(new_order.total_discount),
                "subtotal_before_discount": str(round(discount_result["subtotal_before_discount"], 2)),
                "free_shipping": discount_result.get("free_shipping", False),
                "discount_breakdown": discount_result.get("discount_breakdown", []),
                "winning_rule": winning_rule,
                "simple_bogo": discount_result.get("simple_bogo", False),
                "bogo_free_note": discount_result.get("bogo_free_note"),
                "items": [
                    serialize_order_item(db, item) for item in order_items
                ],
                "created_at": new_order.created_at.isoformat(),
                "updated_at": new_order.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Order Creation Failed | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order.",
        )


@router.get("/{order_id}/adjustments", status_code=status.HTTP_200_OK)
async def get_order_adjustments(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(gt=0),
):
    """
    Get all manual adjustments for an order.
    GET /admin/orders/{order_id}/adjustments
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        adjustments = (
            db.query(OrderAdjustment)
            .filter(OrderAdjustment.order_id == order_id)
            .order_by(OrderAdjustment.created_at.desc())
            .all()
        )

        result = []
        for adj in adjustments:
            admin_user = None
            if adj.admin_user_id:
                admin_user = db.query(User).filter(User.id == adj.admin_user_id).first()

            result.append({
                "id": adj.id,
                "order_id": adj.order_id,
                "admin_user_id": adj.admin_user_id,
                "admin_name": admin_user.full_name if admin_user else None,
                "admin_phone": admin_user.phone_number if admin_user else None,
                "adjustment_type": adj.adjustment_type,
                "value_type": adj.value_type or "flat",
                "amount": str(adj.amount),
                "reason": adj.reason,
                "before_total": str(adj.before_total) if adj.before_total is not None else None,
                "after_total": str(adj.after_total) if adj.after_total is not None else None,
                "created_at": adj.created_at.isoformat(),
            })

        logger.info(
            f"📋 Order Adjustments Retrieved | "
            f"Order={order_id} | "
            f"Count={len(result)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order adjustments retrieved successfully.",
            "order_id": order_id,
            "order_number": order.order_number,
            "current_total": str(order.total_price),
            "adjustments": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving order adjustments | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order adjustments.",
        )


@router.post("/{order_id}/adjustments", status_code=status.HTTP_201_CREATED)
async def create_order_adjustment(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(gt=0),
    adjustment_data: OrderAdjustmentCreate = None,
):
    """
    Manually apply a discount / charge to an existing order.
    POST /admin/orders/{order_id}/adjustments

    - `manual_discount`: reduces order total by amount (BDT or % of current total)
    - `manual_charge`: increases order total by amount (BDT or % of current total)
    - `rounding`: rounds the total to the nearest integer

    value_type:
      - 'flat':  `value` is the fixed BDT amount to subtract/add
      - 'percentage': `value` is a % applied to the CURRENT order total (after automated discounts)
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        adjustment_type = adjustment_data.adjustment_type or "manual_discount"
        value_type = adjustment_data.value_type or "flat"
        value = float(adjustment_data.value)
        reason = adjustment_data.reason

        # Reason is REQUIRED for all manual adjustments (accountability)
        if not reason or not reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason/Note is required for manual order adjustments.",
            )

        current_total = float(order.total_price)

        # Convert percentage value to the actual amount based on current total
        if value_type == "percentage":
            if adjustment_type in ("manual_discount", "manual_charge"):
                if value < 0 or value > 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Percentage value must be between 0 and 100.",
                    )
                amount = current_total * (value / 100.0)
            else:
                amount = value
        else:
            amount = value

        if adjustment_type == "manual_discount":
            new_total = current_total - amount
        elif adjustment_type == "manual_charge":
            new_total = current_total + amount
        elif adjustment_type == "rounding":
            # Rounding: amount is difference to round to nearest integer
            new_total = round(current_total)
            amount = abs(new_total - current_total)
            if new_total < current_total:
                adjustment_type = "rounding_down"
            else:
                adjustment_type = "rounding_up"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid adjustment_type. Must be 'manual_discount', 'manual_charge', or 'rounding'.",
            )
        # Create adjustment entry (audit log)
        adjustment = OrderAdjustment(
            order_id=order_id,
            admin_user_id=admin.id,
            adjustment_type=adjustment_type,
            value_type=value_type,
            amount=round(amount, 2),
            reason=reason,
            before_total=round(current_total, 2),
            after_total=round(new_total, 2),
        )
        db.add(adjustment)

        # Update the order total
        order.total_price = round(new_total, 2)

        db.commit()
        db.refresh(adjustment)
        db.refresh(order)

        logger.info(
            f"✅ Order Adjustment Applied | "
            f"Order={order_id} | "
            f"Type={adjustment_type} | "
            f"Amount=৳{amount:.2f} | "
            f"Total: {current_total:.2f} -> {new_total:.2f} | "
            f"Admin={admin.phone_number} | "
            f"Reason={reason}"
        )

        return {
            "message": "Order adjustment applied successfully.",
            "adjustment": {
                "id": adjustment.id,
                "order_id": adjustment.order_id,
                "admin_user_id": adjustment.admin_user_id,
                "adjustment_type": adjustment.adjustment_type,
                "value_type": value_type,
                "value": str(value),
                "amount": str(round(amount, 2)),
                "reason": adjustment.reason,
                "before_total": str(adjustment.before_total),
                "after_total": str(adjustment.after_total),
                "created_at": adjustment.created_at.isoformat(),
            },
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "total_price": str(order.total_price),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Order Adjustment Failed | "
            f"Error={str(e)} | "
            f"Order={order_id} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply order adjustment.",
        )


@router.delete("/{order_id}/adjustments/{adjustment_id}", status_code=status.HTTP_200_OK)
async def delete_order_adjustment(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(gt=0),
    adjustment_id: int = Path(gt=0),
):
    """
    Remove a manual adjustment (reverses the effect on the order total).
    DELETE /admin/orders/{order_id}/adjustments/{adjustment_id}
    """
    try:
        adjustment = (
            db.query(OrderAdjustment)
            .filter(OrderAdjustment.id == adjustment_id, OrderAdjustment.order_id == order_id)
            .first()
        )
        if not adjustment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adjustment not found.")

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        # Reverse the adjustment
        current_total = float(order.total_price)
        adjustment_amount = float(adjustment.amount)
        adjustment_type = adjustment.adjustment_type

        if adjustment_type in ("manual_discount", "rounding_down"):
            # Discount was applied, so reversing it increases the total back
            new_total = current_total + adjustment_amount
        elif adjustment_type in ("manual_charge", "rounding_up"):
            # Charge was applied, so reversing it decreases the total back
            new_total = current_total - adjustment_amount
        else:
            new_total = current_total

        if new_total < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete adjustment: order would become negative.",
            )

        order.total_price = round(new_total, 2)

        db.delete(adjustment)
        db.commit()
        db.refresh(order)

        logger.info(
            f"✅ Adjustment Deleted | "
            f"Order={order_id} | "
            f"Adjustment={adjustment_id} | "
            f"New Total={new_total:.2f} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order adjustment deleted successfully.",
            "order": {
                "id": order.id,
                "order_number": order.order_number,
                "total_price": str(order.total_price),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Adjustment Delete Failed | "
            f"Error={str(e)} | "
            f"Order={order_id} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete adjustment.",
        )


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
async def delete_order(
    db: db_dependency, admin: admin_dependency, order_id: int = Path(gt=0)
):
    """
    Delete order (cascade delete order items).
    DELETE /admin/orders/{order_id}
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            logger.warning(
                f"⚠️ Order Delete Failed | "
                f"ID={order_id} not found | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        order_number = order.order_number

        db.delete(order)
        db.commit()

        logger.info(
            f"✅ Order Deleted | "
            f"ID={order_id} | "
            f"Order Number={order_number} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Order deleted successfully.",
            "deleted_order_id": order_id,
            "deleted_order_number": order_number,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ Order Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete order.",
        )

# ==========================================================
# Invoice PDF Download (system generated)
# ==========================================================

# One-time short-lived download tickets. Lets the frontend trigger a direct
# browser navigation (no XHR -> no CORS / download-manager conflicts) while
# still requiring admin authentication.
#
# NOTE: Tickets are intentionally RE-USABLE within their TTL. Download
# managers (e.g. IDM) fire several parallel/retry requests for one download;
# single-use tickets break them and trigger auth pop-ups.
_invoice_tickets = {}

TICKET_TTL_SECONDS = 300


def _validate_invoice_token(authorization: str | None) -> bool:
    """Manually validate an admin JWT from the Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return False
    try:
        from jose import jwt as jose_jwt
        from app.core.config import settings as app_settings

        payload = jose_jwt.decode(
            authorization.split(" ", 1)[1],
            app_settings.SECRET_KEY,
            algorithms=[app_settings.ALGORITHM],
        )
        return payload.get("role") == "admin"
    except Exception:
        return False


@router.post("/{order_id}/invoice-ticket", status_code=status.HTTP_200_OK)
async def create_invoice_ticket(
    db: db_dependency,
    admin: admin_dependency,
    order_id: int = Path(..., gt=0),
):
    """
    Create a download ticket for an order invoice.
    POST /admin/orders/{order_id}/invoice-ticket

    The returned ticket is valid for 5 minutes and can be used multiple
    times (download managers fire parallel/retry requests) via:
    GET /admin/orders/{order_id}/invoice?ticket=<ticket>
    """
    import uuid
    from time import time as now_ts

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    # Lazy cleanup of expired tickets so the dict stays small.
    current = now_ts()
    for t in [k for k, v in _invoice_tickets.items() if v["expires"] < current]:
        _invoice_tickets.pop(t, None)

    ticket = uuid.uuid4().hex
    _invoice_tickets[ticket] = {
        "order_id": order_id,
        "expires": current + TICKET_TTL_SECONDS,
    }

    return {"ticket": ticket}


@router.get("/{order_id}/invoice", status_code=status.HTTP_200_OK)
async def download_order_invoice(
    db: db_dependency,
    order_id: int = Path(..., gt=0),
    ticket: str = Query(None),
    authorization: str | None = None,
):
    """
    Generate and download the invoice PDF for an order.

    Auth (either one):
    - one-time ticket: GET .../invoice?ticket=<ticket>
    - admin Authorization: Bearer header
    """
    from time import time as now_ts

    authorized_via_ticket = False

    if ticket:
        entry = _invoice_tickets.get(ticket)
        if (
            not entry
            or entry["expires"] < now_ts()
            or entry["order_id"] != order_id
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired download link. Please try again.",
            )
        # Re-usable within TTL - do NOT consume. Download managers fire
        # multiple parallel/retry requests for a single download.
        authorized_via_ticket = True
    elif not _validate_invoice_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .order_by(OrderItem.created_at.asc(), OrderItem.id.asc())
        .all()
    )

    settings_row = db.query(SiteSettings).first()

    try:
        from app.services.invoice_service import build_invoice_pdf

        pdf_bytes = build_invoice_pdf(order, items, settings_row)
    except Exception as e:
        logger.error(f"❌ Invoice generation failed | Order={order.order_number} | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate invoice PDF.",
        )

    logger.info(
        f"🧾 Invoice Generated | Order={order.order_number} | "
        f"Auth={'ticket' if authorized_via_ticket else 'header'}"
    )

    filename = f"invoice-{order.order_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
