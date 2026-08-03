from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # CORS
    CORS_ORIGINS: List[str]

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # OTP
    OTP_EXPIRE_MINUTES: int

    # Default Admin
    DEFAULT_ADMIN_FIRST_NAME: str
    DEFAULT_ADMIN_LAST_NAME: str
    DEFAULT_ADMIN_PHONE_NUMBER: str
    DEFAULT_ADMIN_EMAIL: str
    DEFAULT_ADMIN_PASSWORD: str

    # Brevo Email
    BREVO_API_KEY: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value


settings = Settings()
