"""Schema definitions for responses / requests."""

from datetime import datetime
from typing import (
    List,
    Optional,
)

from pydantic import BaseModel


class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int


class PutFileResponse(BaseModel):
    file_path: str
    message: str


class GetFilesQueryParams(BaseModel):
    page_size: int = 10
    directory: Optional[str] = ""
    page_token: Optional[str] = None


class GetFilesResponse(BaseModel):
    files: List[FileMetadata]
    next_page_token: Optional[str]
