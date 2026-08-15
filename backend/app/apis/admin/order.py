import json
from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import or_
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
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.utils.variant_generator import find_matching_variant, compute_product_in_stock, build_attributes_display, resolve_attrs_display
from app.utils.order_snapshots import (
    build_user_snapshot,
    build_product_snapshot,
    build_variant_snapshot,
    parse_snapshot,
    serialize_order_item,
)

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
    skip: int = 0,
    limit: int = 100,
):
    """
    Get all orders (optional status filter).
    GET /admin/orders
    GET /admin/orders?status=pending
    """
    try:
        query = db.query(Order)

        if status_filter:
            query = query.filter(Order.status == status_filter)

        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        total = query.count()

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
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                }
                for order in orders
            ],
        }

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

        # Update user email if provided
        if order_data.email and not user.email:
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

        # Capture existing snapshots BEFORE deleting old items
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

        # Delete old items
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        # Create new items
        total_price = 0
        for item in order_data.items:
            if item.product_id is None:
                # Product was deleted - keep original snapshot from existing order items
                fallback = old_snapshot_map.get(None)
                if not fallback:
                    # Try to find any snapshot with null product_id
                    for key, snap in old_snapshot_map.items():
                        if key is None:
                            fallback = snap
                            break

                if not fallback:
                    # No existing snapshot to fall back to - skip
                    continue

                unit_price = fallback["unit_price"]
                line_total = unit_price * item.quantity
                total_price += line_total
                db.add(OrderItem(
                    order_id=order_id, product_id=None, quantity=item.quantity,
                    unit_price=unit_price, price_at_purchase=line_total, selected_attributes=item.selected_attributes or fallback["selected_attributes"],
                    product_snapshot=fallback["product_snapshot"],
                    variant_snapshot=fallback["variant_snapshot"],
                ))
                continue

            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {item.product_id} not found.")
            if not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is not available.")
            if not compute_product_in_stock(db, item.product_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is out of stock.")

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total
            db.add(OrderItem(
                order_id=order_id, product_id=item.product_id, quantity=item.quantity,
                unit_price=unit_price, price_at_purchase=line_total, selected_attributes=item.selected_attributes,
                product_snapshot=build_product_snapshot(db, item.product_id),
                variant_snapshot=build_variant_snapshot(db, item.product_id, item.selected_attributes)
            ))

        order.total_price = total_price
        db.commit()
        db.refresh(order)
        return {"message": "Order updated successfully.", "order": {"id": order.id, "order_number": order.order_number, "total_price": str(order.total_price)}}

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
        if new_status in ("returned", "cancelled") and old_status != new_status:
            order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            for item in order_items:
                try:
                    attrs = json.loads(item.selected_attributes) if item.selected_attributes else {}
                    variant = find_matching_variant(db, item.product_id, resolve_attrs_display(db, attrs))
                    if variant:
                        variant.stock_quantity += item.quantity
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

            if not compute_product_in_stock(db, item.product_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is out of stock.",
                )

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total

            order_items_data.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "price_at_purchase": line_total,
                    "selected_attributes": item.selected_attributes,
                }
            )

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
                unit_price=item_data["unit_price"],
                price_at_purchase=item_data["price_at_purchase"],
                selected_attributes=item_data["selected_attributes"],
                product_snapshot=build_product_snapshot(db, product_id),
                variant_snapshot=build_variant_snapshot(
                    db, product_id, item_data["selected_attributes"]
                ),
            )
            db.add(order_item)

            # Decrement variant stock on order creation
            try:
                attrs = json.loads(item_data["selected_attributes"]) if item_data["selected_attributes"] else {}
                variant = find_matching_variant(db, item_data["product_id"], resolve_attrs_display(db, attrs))
                if variant and variant.stock_quantity >= item_data["quantity"]:
                    variant.stock_quantity -= item_data["quantity"]
                    db.add(variant)
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue

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


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_orders(
    db: db_dependency,
    admin: admin_dependency,
    type: str = Query(..., description="Search type: phone, name, address, or order_number"),
    value: str = Query(..., description="Search value"),
):
    """
    Search orders by phone, name, address, or order number.
    GET /admin/orders/search?type=phone&value=01700000000
    GET /admin/orders/search?type=name&value=Rahim
    GET /admin/orders/search&type=address&value=Mirpur
    GET /admin/orders/search&type=order_number&value=ORD-20250809-7C0D2
    """
    try:
        valid_types = ["phone", "name", "address", "order_number"]

        if type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search type. Must be one of: {', '.join(valid_types)}",
            )

        search_term = f"%{value}%"

        if type == "phone":
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

        orders = query.order_by(Order.created_at.desc()).all()

        logger.info(
            f"🔍 Orders Searched | Type={type} | Value={value} | Count={len(orders)} | Admin={admin.phone_number}"
        )

        return {
            "message": "Orders retrieved successfully.",
            "search_type": type,
            "search_value": value,
            "orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "full_name": order.full_name,
                    "phone_number": order.phone_number,
                    "email": order.email,
                    "district": order.district,
                    "address": order.address,
                    "status": order.status,
                    "total_price": str(order.total_price),
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
