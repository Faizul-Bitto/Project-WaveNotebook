import os
from app.core.logger import logger
from app.services.file_storage import get_file_storage


async def upload_file_to_storage(file, product_id: int):
    """
    Upload file to configured storage provider.
    Returns: file_url or None if failed
    """

    try:
        if not file.filename:
            return None

        # Validate file
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            logger.warning(f"⚠️ Invalid file extension | File={file.filename}")
            return None

        # Read file content
        content = await file.read()

        # Get storage provider and upload
        storage = get_file_storage()
        file_url = await storage.upload(
            file_content=content,
            file_name=file.filename,
            folder="wave_notebook",
            product_id=product_id,
        )

        return file_url

    except Exception as e:
        logger.error(
            f"❌ File upload failed | " f"File={file.filename} | " f"Error={str(e)}"
        )
        return None


async def delete_file_from_storage(file_url: str) -> bool:
    """
    Delete file from configured storage provider.
    """
    try:
        storage = get_file_storage()
        return await storage.delete(file_url)

    except Exception as e:
        logger.error(f"❌ File delete failed | " f"URL={file_url} | " f"Error={str(e)}")
        return False
