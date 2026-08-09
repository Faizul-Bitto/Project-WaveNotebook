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
from app.schemas.order import OrderCreate, OrderStatusUpdate

router = APIRouter(
    prefix="/admin/orders",
    tags=["Admin - Orders"],
)


def calculate_unit_price(db, product_id: int, selected_attributes: str = None) -> float:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return 0
    total_price = float(product.base_price)
    if selected_attributes:
        try:
            attrs = json.loads(selected_attributes)
            for attr_id_str, option_value in attrs.items():
                try:
                    attr_id = int(attr_id_str)
                    option = db.query(AttributeOption).filter(
                        AttributeOption.id == option_value,
                        AttributeOption.attribute_id == attr_id
                    ).first()
                    if option and option.additional_price:
                        total_price += float(option.additional_price)
                except (ValueError, TypeError):
                    continue
        except json.JSONDecodeError:
            pass
    return total_price


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

        items_data = []
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()

            # Build selected attributes display
            selected_attrs_display = None
            if item.selected_attributes:
                try:
                    attrs = json.loads(item.selected_attributes)
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

            items_data.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else f"Product #{item.product_id}",
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "price_at_purchase": str(item.price_at_purchase),
                    "selected_attributes": item.selected_attributes,
                    "selected_attributes_display": selected_attrs_display,
                }
            )

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
            user = User(phone_number=order_data.phone_number, email=None, role="customer", password=None)
            db.add(user)
            db.flush()

        # Update order fields
        order.user_id = user.id
        order.full_name = order_data.full_name
        order.phone_number = order_data.phone_number
        order.district = order_data.district
        order.thana = order_data.thana or ""
        order.note = order_data.note
        order.address = order_data.address

        # Delete old items
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        # Create new items
        total_price = 0
        for item in order_data.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID {item.product_id} not found.")
            if not product.is_active:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is not available.")
            if not product.is_in_stock:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Product '{product.name}' is out of stock.")

            unit_price = calculate_unit_price(db, item.product_id, item.selected_attributes)
            line_total = unit_price * item.quantity
            total_price += line_total
            db.add(OrderItem(
                order_id=order_id, product_id=item.product_id, quantity=item.quantity,
                unit_price=unit_price, price_at_purchase=line_total, selected_attributes=item.selected_attributes
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

        valid_statuses = ["pending", "called", "confirmed", "processing", "shipped", "delivered", "cancelled"]

        if status_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        old_status = order.status
        order.status = status_data.status

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
                email=None,
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

            if not product.is_in_stock:
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

        # Create order
        new_order = Order(
            order_number=order_number,
            user_id=user.id,
            full_name=order_data.full_name,
            phone_number=order_data.phone_number,
            district=order_data.district,
            thana=order_data.thana or "",
            note=order_data.note,
            address=order_data.address,
            status="pending",
            total_price=total_price,
        )

        db.add(new_order)
        db.flush()

        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                price_at_purchase=item_data["price_at_purchase"],
                selected_attributes=item_data["selected_attributes"],
            )
            db.add(order_item)

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
                "district": new_order.district,
                "thana": new_order.thana or "",
                "note": new_order.note,
                "address": new_order.address,
                "status": new_order.status,
                "total_price": str(new_order.total_price),
                "items": [
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                        "price_at_purchase": str(item.price_at_purchase),
                        "selected_attributes": item.selected_attributes,
                    }
                    for item in order_items
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
