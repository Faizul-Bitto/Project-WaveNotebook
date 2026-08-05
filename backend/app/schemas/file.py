from pydantic import BaseModel
from typing import Optional


class FileCreate(BaseModel):
    file_name: str
    file_url: str


class FileUpdate(BaseModel):
    file_name: Optional[str] = None
    file_url: Optional[str] = None
