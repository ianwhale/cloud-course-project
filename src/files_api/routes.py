"""Route definitions."""

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import (
    FileMetadata,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
)

ROUTER = APIRouter()


@ROUTER.put("/files/{file_path:path}")
async def upload_file(
    request: Request, file_path: str, file: UploadFile, response: Response
) -> PutFileResponse:
    """Upload a file."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    object_already_exists = object_exists_in_s3(
        bucket_name=s3_bucket_name, object_key=file_path
    )

    if object_already_exists:
        response_message = f"Existing file updated at path: /{file_path}"
        response.status_code = status.HTTP_200_OK
    else:
        response_message = f"New file uploaded at path: /{file_path}"
        response.status_code = status.HTTP_201_CREATED

    file_content: bytes = await file.read()

    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=file_path,
        file_content=file_content,
        content_type=file.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )


@ROUTER.get("/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),
) -> GetFilesResponse:
    """List files with pagination."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    if query_params.page_token is None:
        objects, token = fetch_s3_objects_metadata(
            bucket_name=s3_bucket_name,
            prefix=query_params.directory,
            max_keys=query_params.page_size,
        )

    else:
        objects, token = fetch_s3_objects_using_page_token(
            bucket_name=s3_bucket_name,
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


@ROUTER.head("/files/{file_path:path}")
async def get_file_metadata(
    request: Request, file_path: str, response: Response
) -> Response:
    """Retrieve file metadata.

    Note: by convention, HEAD requests MUST NOT return a body in the response.
    """
    get_object_response = fetch_s3_object(
        bucket_name=request.app.state.settings.s3_bucket_name, object_key=file_path
    )

    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK

    return response


@ROUTER.get("/files/{file_path:path}")
async def get_file(request: Request, file_path: str) -> StreamingResponse:
    """Retrieve a file."""
    response = fetch_s3_object(
        bucket_name=request.app.state.settings.s3_bucket_name, object_key=file_path
    )
    return StreamingResponse(
        content=response["Body"], media_type=response["ContentType"]
    )


@ROUTER.delete("/files/{file_path:path}")
async def delete_file(
    request: Request,
    file_path: str,
    response: Response,
) -> Response:
    """Delete a file.

    NOTE: DELETE requests MUST NOT return a body in the response."""
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    if not object_exists_in_s3(bucket_name=s3_bucket_name, object_key=file_path):
        response.status_code = status.HTTP_404_NOT_FOUND

    else:
        delete_s3_object(bucket_name=s3_bucket_name, object_key=file_path)
        response.status_code = status.HTTP_204_NO_CONTENT

    return response
