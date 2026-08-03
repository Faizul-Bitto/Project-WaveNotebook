from pydantic import BaseModel, Field, field_validator
from email_validator import validate_email as validate_email_format


class CreateUserRequest(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    email: str | None = None

    password: str = Field(
        min_length=6,
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        # Validate email format
        validate_email_format(v, check_deliverability=False)
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class ForgotPasswordRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )


class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    otp: str = Field(
        min_length=6,
        max_length=6,
    )


class ResetPasswordRequest(BaseModel):
    phone_number: str = Field(
        min_length=10,
        max_length=20,
    )

    new_password: str = Field(
        min_length=6,
    )
