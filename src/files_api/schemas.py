"""Schema definitions for responses / requests."""

from datetime import datetime
from typing import (
    List,
    Optional,
    Self,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

DEFAULT_GET_FILES_PAGE_SIZE = 10
DEFAULT_GET_FILES_MIN_PAGE_SIZE = 10
DEFAULT_GET_FILES_MAX_PAGE_SIZE = 1000
DEFAULT_GET_FILES_DIRECTORY = ""


class FileMetadata(BaseModel):
    """Represents a file in the filesystem."""

    file_path: str = Field(
        description="The path of the file.",
        json_schema_extra={"example": "path/to/pyproject.toml"},
    )
    last_modified: datetime = Field(
        description="The last modified date of the file.",
        json_schema_extra={"example": "2025-01-25T00:00:00Z"},
    )
    size_bytes: int = Field(
        description="The size of the file in bytes.",
        json_schema_extra={"example": 512},
    )


class PutFileResponse(BaseModel):
    """Response for `PUT /files/:file_path`."""

    file_path: str = Field(
        description="The path of the created file.",
        json_schema_extra={"example": "uploads/document.pdf"},
    )
    message: str = Field(
        description="Success message for the file creation.",
        json_schema_extra={"example": "File uploaded successfully"},
    )


class GetFilesQueryParams(BaseModel):
    """Parameters for `GET /files`."""

    page_size: Optional[int] = Field(
        DEFAULT_GET_FILES_PAGE_SIZE,
        ge=DEFAULT_GET_FILES_MIN_PAGE_SIZE,
        le=DEFAULT_GET_FILES_MAX_PAGE_SIZE,
        description="The number of files to return per page.",
        json_schema_extra={"example": 20},
    )
    directory: Optional[str] = Field(
        DEFAULT_GET_FILES_DIRECTORY,
        description="The directory to filter files by.",
        json_schema_extra={"example": "uploads/images"},
    )
    page_token: Optional[str] = Field(
        None,
        description="Token for retrieving the next page of results.",
        json_schema_extra={"example": "abc123xyz"},
    )

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
    """Response for `GET /files`."""

    files: List[FileMetadata]
    next_page_token: Optional[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "files": [
                    {
                        "file_path": "path/to/pyproject.toml",
                        "last_modified": "2025-01-25T00:00:00Z",
                        "size_bytes": 512,
                    },
                    {
                        "file_path": "path/to/Makefile",
                        "last_modified": "2025-01-25T01:00:00Z",
                        "size_bytes": 201,
                    },
                ],
                "next_page_token": "abc123",
            }
        }
    )
