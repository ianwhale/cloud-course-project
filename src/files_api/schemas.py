"""Schema definitions for responses / requests."""

from datetime import datetime
from typing import (
    List,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
)

DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 1000
DEFAULT_GET_FILES_DIRECTORY = ""


class FileMetadata(BaseModel):
    file_path: str
    last_modified: datetime
    size_bytes: int


class PutFileResponse(BaseModel):
    file_path: str
    message: str


class GetFilesQueryParams(BaseModel):
    page_size: int = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    )
    directory: str = DEFAULT_GET_FILES_DIRECTORY
    page_token: Optional[str] = None


class GetFilesResponse(BaseModel):
    files: List[FileMetadata]
    next_page_token: Optional[str]
