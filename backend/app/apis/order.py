from datetime import datetime
import json
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import or_
from starlette import status

from app.core.logger import logger
from app.dependencies.database import db_dependency
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.product_attribute import ProductAttribute
from app.models.product_attribute_option import ProductAttributeOption
from app.models.attribute_option import AttributeOption
from app.models.attribute import Attribute
from app.models.product_variant import ProductVariant
from app.schemas.order import OrderCreate
from app.utils.variant_generator import find_matching_variant, compute_product_in_stock

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


def generate_order_number() -> str:
    """
    Generate unique order number.
    Format: ORD-YYYYMMDD-XXXXX
    """
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = str(uuid.uuid4()).replace("-", "").upper()[:5]
    return f"ORD-{date_str}-{random_str}"


def calculate_unit_price(db, product_id: int, selected_attributes: str = None) -> float:
    """
    Calculate the unit price for an item using the variant system.
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


def build_attributes_display(db, selected_attributes: str = None) -> Optional[str]:
    """
    Build a human-readable string of selected attributes.
    Example: "Size: XL, Color: Red"
    """
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(db: db_dependency, order_data: OrderCreate):
    """
    Create order. Auto-creates user if phone number doesn't exist.
    POST /orders
    """
    try:
        # Validate items
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
                password=None,  # Cash-on-delivery: no password needed
            )
            db.add(user)
            db.flush()
            logger.info(f"✅ New User Auto-Created | User ID={user.id} | Phone={user.phone_number}")

        # Generate unique order number
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

            if not compute_product_in_stock(db, product.id):
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
                        detail=f"Please select the following option(s) for '{product.name}': {', '.join(missing_attrs)}.",
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
            f"✅ Order Created | "
            f"Order Number={new_order.order_number} | "
            f"User ID={user.id} | "
            f"Phone={user.phone_number} | "
            f"Total={total_price} | "
            f"Items={len(order_items_data)}"
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
        logger.error(f"❌ Order Creation Failed | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order.",
        )


@router.get("/track/{phone_number}", status_code=status.HTTP_200_OK)
async def get_orders_by_phone(
    db: db_dependency, phone_number: str = Path(...)
):
    """
    Get orders by phone number.
    GET /orders/track/{phone_number}
    """
    try:
        orders = (
            db.query(Order)
            .filter(Order.phone_number == phone_number)
            .order_by(Order.created_at.desc())
            .all()
        )

        if not orders:
            logger.warning(f"⚠️ No Orders Found | Phone={phone_number}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No orders found for this phone number.",
            )

        result = []
        for order in orders:
            order_items = (
                db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            )

            items_data = []
            for item in order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                items_data.append(
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_name": product.name if product else f"Product #{item.product_id}",
                        "quantity": item.quantity,
                        "unit_price": str(item.unit_price),
                        "price_at_purchase": str(item.price_at_purchase),
                        "selected_attributes": item.selected_attributes,
                        "selected_attributes_display": build_attributes_display(db, item.selected_attributes),
                    }
                )

            result.append(
                {
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
                    "items": items_data,
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                }
            )

        logger.info(f"✅ Orders Retrieved | Phone={phone_number} | Count={len(orders)}")

        return {
            "message": "Orders retrieved successfully.",
            "phone_number": phone_number,
            "orders": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving orders | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders.",
        )


@router.get("/track-number/{order_number}", status_code=status.HTTP_200_OK)
async def get_order_by_number(
    db: db_dependency, order_number: str = Path(...)
):
    """
    Get single order by order number.
    GET /orders/track-number/{order_number}
    """
    try:
        order = db.query(Order).filter(Order.order_number == order_number).first()

        if not order:
            logger.warning(f"⚠️ Order Not Found | Order Number={order_number}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        order_items = (
            db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        )

        items_data = []
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            items_data.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else f"Product #{item.product_id}",
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "price_at_purchase": str(item.price_at_purchase),
                    "selected_attributes": item.selected_attributes,
                    "selected_attributes_display": build_attributes_display(db, item.selected_attributes),
                }
            )

        logger.info(f"✅ Order Retrieved by Number | Order Number={order_number}")

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
                "items": items_data,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving order by number | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order.",
        )


@router.get("/{order_id}", status_code=status.HTTP_200_OK)
async def get_order_by_id(db: db_dependency, order_id: int = Path(gt=0)):
    """
    Get single order details.
    GET /orders/{id}
    """
    try:
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            logger.warning(f"⚠️ Order Not Found | ID={order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
            )

        order_items = (
            db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        )

        items_data = []
        for item in order_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            items_data.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": product.name if product else f"Product #{item.product_id}",
                    "quantity": item.quantity,
                    "unit_price": str(item.unit_price),
                    "price_at_purchase": str(item.price_at_purchase),
                    "selected_attributes": item.selected_attributes,
                    "selected_attributes_display": build_attributes_display(db, item.selected_attributes),
                }
            )

        logger.info(f"✅ Order Retrieved | ID={order.id}")

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
                "items": items_data,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving order | Error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order.",
        )