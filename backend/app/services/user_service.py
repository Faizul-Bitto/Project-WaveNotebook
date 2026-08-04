from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.core.security import (
    bcrypt_context,
    generate_otp,
    hash_password,
    verify_password,
)
from app.core.sms import send_sms
from app.models.otp import OTP
from app.models.user import User
from app.schemas.user import (
    UpdatePhoneRequest,
    UpdateUserRequest,
    UserUpdatePasswordRequest,
    VerifyPhoneUpdateRequest,
)
from app.utils.datetime import ensure_timezone_aware


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
        Update user profile (name and email only, not phone).
        """

        # Phone number is the base identifier
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
    def request_phone_update(
        db: Session,
        user: User,
        request: UpdatePhoneRequest,
    ) -> dict:
        """
        Request phone number update - sends OTP to new phone number.
        """

        # Check if new phone number is different
        if request.phone_number == user.phone_number:
            raise ValueError("New phone number is the same as current.")

        # Check if new phone number is already registered
        existing_phone = (
            db.query(User)
            .filter(User.phone_number == request.phone_number)
            .first()
        )

        if existing_phone:
            raise ValueError("Phone number already registered.")

        # Disable previous OTPs for phone update
        db.query(OTP).filter(
            OTP.user_id == user.id,
            OTP.purpose == "phone_update",
            OTP.is_used.is_(False),
        ).update({OTP.is_used: True})

        db.commit()

        # Generate OTP
        otp = generate_otp()

        # Create OTP record
        otp_record = OTP(
            user_id=user.id,
            phone_number=request.phone_number, 
            code=hash_password(otp),
            purpose="phone_update",
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            ),
        )

        db.add(otp_record)
        db.commit()
        db.refresh(otp_record)

        try:
            # Send OTP to NEW phone number
            send_sms(
                phone_number=request.phone_number,
                message=(
                    f"Your phone number update OTP is {otp}. "
                    f"Expires in {settings.OTP_EXPIRE_MINUTES} minutes."
                ),
            )

            logger.info(
                f"📱 Phone Update OTP Sent | User ID={user.id} | New Phone={request.phone_number}"
            )

        except Exception:
            logger.exception(
                f"❌ Failed To Send Phone Update OTP | User ID={user.id} | New Phone={request.phone_number}"
            )
            raise RuntimeError("Unable to send OTP. Please try again later.")

        return {
            "message": "OTP sent to new phone number for verification.",
            "phone_number": request.phone_number,
        }

    @staticmethod
    def verify_phone_update(
        db: Session,
        user: User,
        request: VerifyPhoneUpdateRequest,
    ) -> dict:
        """
        Verify OTP for phone number update.
        """

        # Find the most recent unused OTP for phone update
        otp_record = (
            db.query(OTP)
            .filter(
                OTP.user_id == user.id,
                OTP.purpose == "phone_update",
                OTP.is_used.is_(False),
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

        if not otp_record:
            raise ValueError("No phone update request found. Please request OTP first.")

        if datetime.now(timezone.utc) > ensure_timezone_aware(otp_record.expires_at):
            raise ValueError("OTP expired.")

        if not verify_password(request.otp, otp_record.code):
            raise ValueError("Invalid OTP.")

        # Mark OTP as verified
        otp_record.verified = True
        db.commit()

        logger.info(
            f"✅ Phone Update OTP Verified | User ID={user.id} | New Phone={otp_record.phone_number}"
        )

        return {
            "message": "Phone number verified successfully.",
            "phone_number": otp_record.phone_number,
        }

    @staticmethod
    def confirm_phone_update(
        db: Session,
        user: User,
        verified_phone_number: str,
    ) -> dict:
        """
        Confirm and update phone number after OTP verification.
        """

        # Find the verified OTP
        otp_record = (
            db.query(OTP)
            .filter(
                OTP.user_id == user.id,
                OTP.purpose == "phone_update",
                OTP.verified.is_(True),
                OTP.is_used.is_(False),
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

        if not otp_record:
            raise ValueError("Please verify OTP first.")

        if otp_record.phone_number != verified_phone_number:
            raise ValueError("Phone number mismatch.")

        # Update user's phone number
        user.phone_number = verified_phone_number

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.verified = False

        db.commit()
        db.refresh(user)

        logger.info(
            f"🔐 Phone Number Updated | User ID={user.id} | New Phone={user.phone_number}"
        )

        return {
            "message": "Phone number updated successfully.",
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