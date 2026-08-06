import boto3
import os
from typing import Optional
from app.core.config import settings
from app.core.logger import logger
from app.services.file_storage.base import FileStorageService


class S3Storage(FileStorageService):
    """
    AWS S3 file storage implementation.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """
        Lazily create the S3 client to avoid import-time failures.
        """
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
            )
        return self._client

    async def upload(
        self, file_content: bytes, file_name: str, folder: str, product_id: int
    ) -> Optional[str]:
        """
        Upload file to S3.
        """
        try:
            # Generate S3 key
            s3_key = f"{folder}/product_{product_id}/{file_name}"

            # Upload to S3
            self.client.put_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(file_name),
            )

            # Generate file URL
            if settings.AWS_S3_ENDPOINT_URL:
                # For custom S3-like services (MinIO, etc)
                file_url = f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_S3_BUCKET_NAME}/{s3_key}"
            else:
                # For AWS S3
                file_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{s3_key}"

            logger.info(f"✅ S3 Upload Success | " f"URL={file_url}")
            return file_url

        except Exception as e:
            logger.error(
                f"❌ S3 Upload Failed | " f"File={file_name} | " f"Error={str(e)}"
            )
            return None

    async def delete(self, file_url: str) -> bool:
        """
        Delete file from S3.
        """
        try:
            s3_key = self.get_public_id(file_url)

            self.client.delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=s3_key)

            logger.info(f"✅ S3 Delete Success | " f"S3 Key={s3_key}")
            return True

        except Exception as e:
            logger.error(f"❌ S3 Delete Failed | " f"Error={str(e)}")
            return False

    def get_public_id(self, file_url: str) -> str:
        """
        Extract S3 key from file URL.
        """
        # Remove domain and get the key
        return file_url.split(f"{settings.AWS_S3_BUCKET_NAME}/")[-1]

    def _get_content_type(self, file_name: str) -> str:
        """
        Get MIME type based on file extension.
        """
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return content_types.get(ext, "application/octet-stream")

    def check_connection(self) -> bool:
        """
        Check if S3 is reachable/configured.
        """
        try:
            # Verify credentials by listing buckets
            self.client.list_buckets()
            return True

        except Exception as e:
            logger.error(f"❌ S3 Connection Check Failed | Error={str(e)}")
            return False
