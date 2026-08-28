import cloudinary.uploader
import os
import uuid
from datetime import datetime
from typing import Optional
from app.core.config import settings
from app.core.logger import logger
from app.services.file_storage.base import FileStorageService

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


class CloudinaryStorage(FileStorageService):
    """
    Cloudinary file storage implementation.
    """

    async def upload(
        self, file_content: bytes, file_name: str, folder: str, product_id: int
    ) -> Optional[str]:
        """
        Upload file to Cloudinary.
        """
        try:
            # Build a unique public_id so every upload gets a fresh URL.
            # Re-using the original filename would overwrite the same asset and
            # browsers/CDNs would keep serving the cached (old) image.
            base_name = os.path.splitext(file_name)[0]
            unique_id = (
                f"{base_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                f"_{uuid.uuid4().hex[:8]}"
            )

            upload_result = cloudinary.uploader.upload(
                file_content,
                folder=f"{folder}/product_{product_id}",
                public_id=unique_id,
                overwrite=True,
                invalidate=True,
                resource_type="auto",
            )

            file_url = upload_result["secure_url"]
            logger.info(f"✅ Cloudinary Upload Success | " f"URL={file_url}")
            return file_url

        except Exception as e:
            logger.error(
                f"❌ Cloudinary Upload Failed | "
                f"File={file_name} | "
                f"Error={str(e)}"
            )
            return None

    async def delete(self, file_url: str) -> bool:
        """
        Delete file from Cloudinary.
        """
        try:
            public_id = self.get_public_id(file_url)
            cloudinary.uploader.destroy(public_id)

            logger.info(f"✅ Cloudinary Delete Success | " f"Public ID={public_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Cloudinary Delete Failed | " f"Error={str(e)}")
            return False

    def get_public_id(self, file_url: str) -> str:
        """
        Extract public ID from Cloudinary URL.
        Format: https://res.cloudinary.com/cloud/image/upload/v123/folder/filename
        """
        # Remove file extension and get the path
        path = file_url.split("/upload/")[-1]  # Get path after /upload/
        return path.rsplit(".", 1)[0]  # Remove extension

    def check_connection(self) -> bool:
        """
        Check if Cloudinary is reachable/configured.
        """
        try:
            import cloudinary.api

            # Verify credentials by fetching account usage
            cloudinary.api.usage()
            return True

        except Exception as e:
            logger.error(f"❌ Cloudinary Connection Check Failed | Error={str(e)}")
            return False
