from abc import ABC, abstractmethod
from typing import Optional


class FileStorageService(ABC):
    """
    Abstract base class for file storage providers.
    """

    @abstractmethod
    async def upload(
        self, file_content: bytes, file_name: str, folder: str, product_id: int
    ) -> Optional[str]:
        """
        Upload file and return URL.
        Returns: file_url or None if failed
        """
        pass

    @abstractmethod
    async def delete(self, file_url: str) -> bool:
        """
        Delete file from storage.
        Returns: True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_public_id(self, file_url: str) -> str:
        """
        Extract public ID from file URL for deletion.
        """
        pass
