"""Schema definitions for responses / requests."""

from datetime import datetime
from typing import (
    List,
    Optional,
    Self,
)

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)

DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 1000
DEFAULT_GET_FILES_DIRECTORY = ""


class FileMetadata(BaseModel):
    """Represents a file in S3."""

    file_path: str
    last_modified: datetime
    size_bytes: int


class PutFileResponse(BaseModel):
    """Schema for the result of a file creation."""

    file_path: str
    message: str


class GetFilesQueryParams(BaseModel):
    """Schema for the input of a get files query."""

    page_size: Optional[int] = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
    )
    directory: Optional[str] = DEFAULT_GET_FILES_DIRECTORY
    page_token: Optional[str] = None

    @model_validator(mode="after")
    def check_page_token_only_argument_if_set(self) -> Self:
        if self.page_token is not None:
            get_files_query_params = self.model_dump(exclude_unset=True)

            page_size_set = "page_size" in get_files_query_params.keys()
            directory_set = "directory" in get_files_query_params.keys()

            if page_size_set or directory_set:
                raise ValueError(
                    "page_token is mutually exclusive with page_size and directory"
                )

        return self


class GetFilesResponse(BaseModel):
    """Schema for the result of a get files query."""

    files: List[FileMetadata]
    next_page_token: Optional[str]
