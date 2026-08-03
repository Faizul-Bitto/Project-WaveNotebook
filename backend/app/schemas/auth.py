from pydantic import BaseModel, EmailStr, Field


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

    email: EmailStr | None = None

    password: str = Field(
        min_length=6,
    )


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
