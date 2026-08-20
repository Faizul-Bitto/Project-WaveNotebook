import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # CORS — stored as Any to prevent pydantic-settings from JSON-decoding env
    # var values before the validator runs. The validator parses into List[str].
    CORS_ORIGINS: Any

    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Default Admin
    DEFAULT_ADMIN_PHONE_NUMBER: str
    DEFAULT_ADMIN_EMAIL: str
    DEFAULT_ADMIN_PASSWORD: str

    # File Storage
    FILE_STORAGE_PROVIDER: str  # "cloudinary" or "s3"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = None
    CLOUDINARY_API_KEY: str = None
    CLOUDINARY_API_SECRET: str = None

    # AWS S3
    AWS_ACCESS_KEY_ID: str = None
    AWS_SECRET_ACCESS_KEY: str = None
    AWS_S3_BUCKET_NAME: str = None
    AWS_S3_REGION: str = None
    AWS_S3_ENDPOINT_URL: str = None  # Optional for custom S3-like services

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any):
        if isinstance(value, str):
            if value.strip().startswith("["):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [origin.strip().rstrip("/") for origin in parsed]
                except (json.JSONDecodeError, TypeError):
                    pass
            return [origin.strip().rstrip("/") for origin in value.split(",")]
        if isinstance(value, list):
            return [str(origin).strip().rstrip("/") for origin in value]
        return value


settings = Settings()
