from datetime import datetime
from tracemalloc import get_object_traceback
from typing import (
    List,
    Optional,
)

from click import Option
from fastapi import (
    Depends,
    FastAPI,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object

#####################
# --- Constants --- #
#####################

S3_BUCKET_NAME = "some-bucket"

APP = FastAPI()

####################################
# --- Request/response schemas --- #
####################################


# read (cRud)
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


##################
# --- Routes --- #
##################


@APP.put("/files/{file_path:path}")
async def upload_file(
    file_path: str, file: UploadFile, response: Response
) -> PutFileResponse:
    """Upload a file."""
    object_already_exists = object_exists_in_s3(
        bucket_name=S3_BUCKET_NAME, object_key=file_path
    )

    if object_already_exists:
        response_message = f"Existing file updated at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_content: bytes = await file.read()

    upload_s3_object(
        bucket_name=S3_BUCKET_NAME,
        object_key=file_path,
        file_content=file_content,
        content_type=file.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )


@APP.get("/files")
async def list_files(query_params: GetFilesQueryParams = Depends()) -> GetFilesResponse:
    """List files with pagination."""
    if query_params.page_token is None:
        objects, token = fetch_s3_objects_metadata(
            bucket_name=S3_BUCKET_NAME,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    else:
        objects, token = fetch_s3_objects_using_page_token(
            bucket_name=S3_BUCKET_NAME,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size,
        )

    files = [
        FileMetadata(
            file_path=str(file["Key"]),
            last_modified=file["LastModified"],
            size_bytes=file["Size"],
        )
        for file in objects
    ]

    return GetFilesResponse(
        files=files,
        next_page_token=token,
    )


@APP.head("/files/{file_path:path}")
async def get_file_metadata(file_path: str, response: Response) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    get_object_response = fetch_s3_object(
        bucket_name=S3_BUCKET_NAME, object_key=file_path
    )

    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK

    return response


@APP.get("/files/{file_path:path}")
async def get_file(file_path: str) -> StreamingResponse:
    """Retrieve a file."""
    response = fetch_s3_object(bucket_name=S3_BUCKET_NAME, object_key=file_path)
    return StreamingResponse(
        content=response["Body"], media_type=response["ContentType"]
    )


@APP.delete("/files/{file_path:path}")
async def delete_file(
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""

    if not object_exists_in_s3(bucket_name=S3_BUCKET_NAME, object_key=file_path):
        response.status_code = status.HTTP_404_NOT_FOUND

    else:
        delete_s3_object(bucket_name=S3_BUCKET_NAME, object_key=file_path)
        response.status_code = status.HTTP_204_NO_CONTENT

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
