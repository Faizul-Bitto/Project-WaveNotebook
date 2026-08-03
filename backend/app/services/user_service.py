from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.security import bcrypt_context
from app.models.user import User
from app.schemas.user import UpdateUserRequest, UserUpdatePasswordRequest


class UserService:

    @staticmethod
    def get_user_profile(user: User) -> dict:
        """
        Get user profile data.
        Phone number is the primary identifier - email is optional.
        """

        logger.info(
            f"👤 Profile Retrieved | ID={user.id} | Phone={user.phone_number} | Role={user.role}"
        )

        return {
            "message": "User profile retrieved successfully.",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
            },
        }

    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        update_request: UpdateUserRequest,
    ) -> dict:
        """
        Update user profile.
        """

        # Phone number is the base identifier - no need to check email uniqueness
        # Email is optional and can be duplicated or null

        user.first_name = update_request.first_name
        user.last_name = update_request.last_name
        user.email = update_request.email

        db.commit()
        db.refresh(user)

        logger.info(
            f"✅ Profile Updated | ID={user.id} | Phone={user.phone_number} | Role={user.role}"
        )

        return {
            "message": "Profile updated successfully.",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "email": user.email,
                "role": user.role,
            },
        }

    @staticmethod
    def update_password(
        user: User,
        update_password_request: UserUpdatePasswordRequest,
    ) -> dict:
        """
        Update user password.
        """

        if not bcrypt_context.verify(
            update_password_request.password,
            user.password,
        ):
            logger.warning(
                f"⚠️ Password Update Failed | Incorrect Password | Phone={user.phone_number} | Role={user.role}"
            )

            raise ValueError("Current password is incorrect.")

        user.password = bcrypt_context.hash(
            update_password_request.new_password,
        )

        # Note: db.commit() and db.refresh() should be done by the caller

        logger.info(
            f"🔐 Password Updated | ID={user.id} | Phone={user.phone_number} | Role={user.role}"
        )

        return {
            "message": "Password updated successfully.",
        }