from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy import or_
from starlette import status

from app.core.logger import logger
from app.dependencies.admin import admin_dependency
from app.dependencies.database import db_dependency
from app.models.user import User
from app.models.order import Order
from app.services.export_service import build_csv, build_xlsx, export_response

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin - Users"],
)


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_users(
    db: db_dependency,
    admin: admin_dependency,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    exclude_role: str = None,
):
    """
    Get all users with optional search by phone, name (via order), or address (via order).
    GET /admin/users?search=01700000000
    """
    try:
        query = db.query(User)

        if search:
            # Search by phone number directly
            phone_match = query.filter(User.phone_number.contains(search))

            # Also search orders by name/address to find linked users
            order_match_ids = (
                db.query(Order.user_id)
                .filter(
                    or_(
                        Order.full_name.contains(search),
                        Order.address.contains(search),
                        Order.district.contains(search),
                    )
                )
                .distinct()
                .all()
            )
            order_user_ids = [row[0] for row in order_match_ids]

            query = db.query(User).filter(
                or_(
                    User.phone_number.contains(search),
                    User.id.in_(order_user_ids) if order_user_ids else False,
                )
            )
        else:
            query = db.query(User)

        if exclude_role:
            query = query.filter(User.role != exclude_role)

        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        total = query.count()

        logger.info(
            f"👥 Users Retrieved | "
            f"Count={len(users)} | "
            f"Search={search or 'None'} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "Users retrieved successfully.",
            "total": total,
            "skip": skip,
            "limit": limit,
            "users": [
                {
                    "id": user.id,
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                }
                for user in users
            ],
        }

    except Exception as e:
        logger.error(
            f"❌ Error retrieving users | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users.",
        )


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_users(
    db: db_dependency,
    admin: admin_dependency,
    search: str = None,
    exclude_role: str = None,
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    """
    Export users (with order count & total spent) to CSV or Excel.
    GET /admin/users/export?format=csv
    """
    try:
        query = db.query(User)

        if search:
            phone_match = query.filter(User.phone_number.contains(search))
            order_match_ids = (
                db.query(Order.user_id)
                .filter(
                    or_(
                        Order.full_name.contains(search),
                        Order.address.contains(search),
                        Order.district.contains(search),
                    )
                )
                .distinct()
                .all()
            )
            order_user_ids = [row[0] for row in order_match_ids]
            query = db.query(User).filter(
                or_(
                    User.phone_number.contains(search),
                    User.id.in_(order_user_ids) if order_user_ids else False,
                )
            )

        if exclude_role:
            query = query.filter(User.role != exclude_role)

        users = query.order_by(User.created_at.desc()).all()

        headers = [
            "User ID",
            "Phone Number",
            "Email",
            "Role",
            "Created At",
            "Updated At",
            "Total Orders",
            "Total Spent (৳)",
        ]

        rows = []
        for user in users:
            orders = db.query(Order).filter(Order.user_id == user.id).all()
            order_count = len(orders)
            total_spent = sum(float(o.total_price or 0) for o in orders)
            rows.append(
                [
                    user.id,
                    user.phone_number,
                    user.email,
                    user.role,
                    user.created_at.strftime("%Y-%m-%d %H:%M")
                    if user.created_at
                    else "",
                    user.updated_at.strftime("%Y-%m-%d %H:%M")
                    if user.updated_at
                    else "",
                    order_count,
                    round(total_spent, 2),
                ]
            )

        fmt = format.lower()
        if fmt == "csv":
            content = build_csv(headers, rows)
            filename = "users.csv"
        else:
            content = build_xlsx(headers, rows, sheet_name="Users")
            filename = "users.xlsx"

        logger.info(
            f"📤 Users Exported | Format={fmt.upper()} | "
            f"Count={len(rows)} | Admin={admin.phone_number}"
        )
        return export_response(content, filename, fmt)

    except Exception as e:
        logger.error(
            f"❌ Error exporting users | Error={str(e)} | Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export users.",
        )


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_by_id(
    db: db_dependency, admin: admin_dependency, user_id: int = Path(gt=0)
):
    """
    Get single user with their orders.
    GET /admin/users/{user_id}
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(
                f"⚠️ User Not Found | "
                f"ID={user_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        # Get user's orders
        orders = (
            db.query(Order)
            .filter(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
            .all()
        )

        logger.info(
            f"👤 User Retrieved | "
            f"ID={user.id} | "
            f"Phone={user.phone_number} | "
            f"Orders={len(orders)} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "User retrieved successfully.",
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
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
                    }
                    for order in orders
                ],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Error retrieving user | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user.",
        )


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user(
    db: db_dependency,
    admin: admin_dependency,
    user_id: int = Path(gt=0),
    phone_number: str = None,
    email: str = None,
):
    """
    Update user phone number / email.
    PUT /admin/users/{user_id}
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(
                f"⚠️ User Not Found | "
                f"ID={user_id} | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        if phone_number:
            # Check phone number uniqueness
            existing = (
                db.query(User)
                .filter(User.phone_number == phone_number, User.id != user_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Phone number already exists.",
                )
            user.phone_number = phone_number

        if email:
            # Check email uniqueness
            existing = (
                db.query(User)
                .filter(User.email == email, User.id != user_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists.",
                )
            user.email = email

        db.commit()
        db.refresh(user)

        logger.info(
            f"✅ User Updated | "
            f"ID={user.id} | "
            f"Phone={user.phone_number} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "User updated successfully.",
            "user": {
                "id": user.id,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ User Update Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user.",
        )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    db: db_dependency, admin: admin_dependency, user_id: int = Path(gt=0)
):
    """
    Delete user (cascade delete orders).
    DELETE /admin/users/{user_id}
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(
                f"⚠️ User Delete Failed | "
                f"ID={user_id} not found | "
                f"Admin={admin.phone_number}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

        phone_number = user.phone_number

        db.delete(user)
        db.commit()

        logger.info(
            f"✅ User Deleted | "
            f"ID={user_id} | "
            f"Phone={phone_number} | "
            f"Admin={admin.phone_number}"
        )

        return {
            "message": "User deleted successfully.",
            "deleted_user_id": user_id,
            "deleted_user_phone": phone_number,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"❌ User Delete Failed | "
            f"Error={str(e)} | "
            f"Admin={admin.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user.",
        )