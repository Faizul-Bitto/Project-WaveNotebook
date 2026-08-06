from app.services.file_storage.base import FileStorageService
from app.services.file_storage.cloudinary_storage import CloudinaryStorage
from app.services.file_storage.s3_storage import S3Storage
from app.core.config import settings


# Factory to get the right storage provider
def get_file_storage() -> FileStorageService:
    """
    Get file storage provider based on configuration.
    """
    provider = settings.FILE_STORAGE_PROVIDER.lower()

    if provider == "s3":
        return S3Storage()
    elif provider == "cloudinary":
        return CloudinaryStorage()
    else:
        raise ValueError(f"Unknown file storage provider: {provider}")


__all__ = ["FileStorageService", "get_file_storage"]
