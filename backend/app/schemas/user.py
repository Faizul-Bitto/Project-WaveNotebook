from pydantic import BaseModel, EmailStr, Field, field_validator
from email_validator import validate_email as validate_email_format


class UserUpdatePasswordRequest(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


class UpdateUserRequest(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        # Validate email format
        validate_email_format(v, check_deliverability=False)
        return v


class UpdatePhoneRequest(BaseModel):
    phone_number: str = Field(min_length=10, max_length=20)


class VerifyPhoneUpdateRequest(BaseModel):
    otp: str = Field(min_length=6, max_length=6)