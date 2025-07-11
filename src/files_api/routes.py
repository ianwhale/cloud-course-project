"""Route definitions."""

import mimetypes
from typing import Annotated

import httpx
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from files_api.generate_files import (
    generate_image,
    generate_text_to_speech,
    get_text_chat_completion,
)
from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import (
    fetch_s3_object,
    fetch_s3_objects_metadata,
    fetch_s3_objects_using_page_token,
    object_exists_in_s3,
)
from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import (
    DEFAULT_GET_FILES_PAGE_SIZE,
    FileMetadata,
    GeneratedFileType,
    GenerateFilesQueryParams,
    GetFilesQueryParams,
    GetFilesResponse,
    PutFileResponse,
    PutGeneratedFileResponse,
)
from files_api.settings import Settings

FILES_ROUTER = APIRouter(tags=["Files"])
GENERATED_FILES_ROUTER = APIRouter(tags=["Generated Files"])

ValidFilePath = Path(
    ...,
    pattern=r"^[^<>:\"|?*\x00-\x1f]+$",
    description="Valid file path without invalid characters",
    examples=["documents/example.txt"],
)


@FILES_ROUTER.put(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_200_OK: {"model": PutFileResponse},
        status.HTTP_201_CREATED: {"model": PutFileResponse},
    },
)
async def upload_file(
    request: Request,
    file_content: UploadFile,
    response: Response,
    file_path: str = ValidFilePath,
) -> PutFileResponse:
    """
    ## Upload a File

    Upload a file to the specified path. If a file already exists at the given path,
    it will be replaced with the new content.

    ### Parameters
    - **file_path**: The destination path where the file should be stored
    - **file_content**: The file content to upload (multipart/form-data)

    ### Response
    - **200 OK**: File was successfully updated (file already existed)
    - **201 Created**: File was successfully uploaded (new file created)

    ### Example
    ```bash
    curl -X PUT "https://api.example.com/v1/files/documents/report.pdf" \
         -F "file=@local-file.pdf"
    ```
    """
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

    file_content_bytes: bytes = await file_content.read()

    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=file_path,
        file_content=file_content_bytes,
        content_type=file_content.content_type,
    )

    return PutFileResponse(
        file_path=file_path,
        message=response_message,
    )


@FILES_ROUTER.get("/v1/files")
async def list_files(
    request: Request,
    query_params: GetFilesQueryParams = Depends(),
) -> GetFilesResponse:
    """
    ## List Files

    Retrieve a paginated list of files stored in the system. Results can be filtered
    by directory and support pagination for efficient browsing of large file collections.

    ### Query Parameters
    - **directory** (optional): Filter files by directory prefix
    - **page_size** (optional): Number of files to return per page (default: 100)
    - **page_token** (optional): Token for retrieving the next page of results

    ### Response
    Returns a list of files with metadata including:
    - File path and name
    - Last modified timestamp
    - File size in bytes
    - Next page token (if more results available)

    ### Example
    ```bash
    # List all files
    curl "https://api.example.com/v1/files"

    # List files in a specific directory
    curl "https://api.example.com/v1/files?directory=documents/"

    # Get next page of results
    curl "https://api.example.com/v1/files?page_token=abc123"
    ```
    """
    s3_bucket_name = request.app.state.settings.s3_bucket_name

    if query_params.page_token is None:
        objects, token = fetch_s3_objects_metadata(
            bucket_name=s3_bucket_name,
            prefix=query_params.directory,
            max_keys=query_params.page_size or DEFAULT_GET_FILES_PAGE_SIZE,
        )

    else:
        objects, token = fetch_s3_objects_using_page_token(
            bucket_name=s3_bucket_name,
            continuation_token=query_params.page_token,
            max_keys=query_params.page_size or DEFAULT_GET_FILES_PAGE_SIZE,
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


def raise_if_file_not_found(bucket_name: str, file_path: str) -> None:
    """Raise an HTTPException is the given file is not in the bucket."""
    if not object_exists_in_s3(bucket_name=bucket_name, object_key=file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found."
        )


@FILES_ROUTER.head(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "headers": {
                "Content-Type": {
                    "description": "The [MIME type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types) of the file.",
                    "example": "text/plain",
                    "schema": {"type": "string"},
                },
                "Content-Length": {
                    "description": "The size of the file in bytes.",
                    "example": 512,
                    "schema": {"type": "integer"},
                },
                "Last-Modified": {
                    "description": "The last modified date of the file.",
                    "example": "Thu, 01 Jan 2022 00:00:00 GMT",
                    "schema": {"type": "string", "format": "date-time"},
                },
            }
        },
    },
)
async def get_file_metadata(
    request: Request,
    response: Response,
    file_path: str = ValidFilePath,
) -> Response:
    """
    ## Get File Metadata

    Retrieve metadata information about a file without downloading the file content.
    This is useful for checking if a file exists and getting its properties.

    ### Parameters
    - **file_path**: The path to the file

    ### Response Headers
    - **Content-Type**: The MIME type of the file
    - **Content-Length**: The size of the file in bytes
    - **Last-Modified**: The last modification date of the file

    ### Status Codes
    - **200 OK**: File exists and metadata retrieved successfully
    - **404 Not Found**: File does not exist

    ### Example
    ```bash
    curl -I "https://api.example.com/v1/files/documents/report.pdf"
    ```

    Note: This endpoint returns only headers, no response body.
    """
    settings = request.app.state.settings

    raise_if_file_not_found(bucket_name=settings.s3_bucket_name, file_path=file_path)

    get_object_response = fetch_s3_object(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )

    response.headers["Content-Type"] = get_object_response["ContentType"]
    response.headers["Content-Length"] = str(get_object_response["ContentLength"])
    response.headers["Last-Modified"] = get_object_response["LastModified"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )
    response.status_code = status.HTTP_200_OK

    return response


@FILES_ROUTER.get(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_200_OK: {
            "description": "The file content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
    },
)
async def get_file(
    request: Request,
    file_path: str = ValidFilePath,
) -> StreamingResponse:
    """
    ## Download a File

    Download the content of a file stored at the specified path. The file is returned
    as a streaming response with the appropriate content type.

    ### Parameters
    - **file_path**: The path to the file to download

    ### Response
    - **200 OK**: File content streamed successfully
    - **404 Not Found**: File does not exist

    ### Response Headers
    - **Content-Type**: The MIME type of the file
    - **Content-Length**: The size of the file in bytes

    ### Example
    ```bash
    # Download a file
    curl "https://api.example.com/v1/files/documents/report.pdf" \
         -o "downloaded-report.pdf"

    # Download and view text file content
    curl "https://api.example.com/v1/files/logs/app.log"
    ```
    """
    settings = request.app.state.settings

    raise_if_file_not_found(settings.s3_bucket_name, file_path)

    response = fetch_s3_object(
        bucket_name=settings.s3_bucket_name, object_key=file_path
    )
    return StreamingResponse(
        content=response["Body"], media_type=response["ContentType"]
    )


@FILES_ROUTER.delete(
    "/v1/files/{file_path:path}",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "File not found for the given `file_path`.",
        },
        status.HTTP_204_NO_CONTENT: {
            "description": "File deleted successfully.",
        },
    },
)
async def delete_file(
    request: Request,
    response: Response,
    file_path: str = ValidFilePath,
) -> Response:
    """
    ## Delete a File

    Permanently delete a file from the specified path. This operation cannot be undone.

    ### Parameters
    - **file_path**: The path to the file to delete

    ### Response
    - **204 No Content**: File deleted successfully
    - **404 Not Found**: File does not exist

    ### Example
    ```bash
    curl -X DELETE "https://api.example.com/v1/files/documents/old-report.pdf"
    ```

    **Warning**: This operation permanently removes the file and cannot be reversed.
    """
    settings = request.app.state.settings

    raise_if_file_not_found(settings.s3_bucket_name, file_path)

    delete_s3_object(bucket_name=settings.s3_bucket_name, object_key=file_path)
    response.status_code = status.HTTP_204_NO_CONTENT

    return response


@GENERATED_FILES_ROUTER.post(
    "/v1/files/generated/{file_path:path}",
    status_code=status.HTTP_201_CREATED,
    summary="AI Generated Files",
    responses={
        status.HTTP_201_CREATED: {
            "model": PutGeneratedFileResponse,
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "examples": {
                        "text": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][0],
                        "image": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][1],
                        "text-to-speech": PutGeneratedFileResponse.model_json_schema()[
                            "examples"
                        ][2],
                    },
                },
            },
        },
    },
)
async def generate_file_using_openai(
    request: Request,
    response: Response,
    query_params: Annotated[GenerateFilesQueryParams, Depends()],
) -> PutGeneratedFileResponse:
    """
    Generate a File using AI.

    Supported file types:
    - **text**: `.txt`
    - **image**: `.png`, `.jpg`, `.jpeg`
    - **text-to-speech**: `.mp3`, `.opus`, `.aac`, `.flac`, `.wav`, `.pcm`

    Note: the generated file type is derived from the file_path extension. So the file_path must have
    an extension matching one of the supported file types in the list above.
    """
    settings: Settings = request.app.state.settings
    s3_bucket_name = settings.s3_bucket_name

    content_type = None

    # generate text
    if query_params.file_type == GeneratedFileType.TEXT:
        file_content = await get_text_chat_completion(prompt=query_params.prompt)
        file_content_bytes: bytes = file_content.encode(
            "utf-8"
        )  # convert string to bytes
        content_type = "text/plain"

    # generate/download an image
    elif query_params.file_type == GeneratedFileType.IMAGE:
        image_url = await generate_image(prompt=query_params.prompt)
        async with httpx.AsyncClient() as client:
            image_response = await client.get(
                image_url
            )  # pylint: disable=missing-timeout
        file_content_bytes = image_response.content

    # generate audio
    else:
        response_audio_file_format = query_params.file_path.split(".")[
            -1
        ]  # the file extension
        file_content_bytes, content_type = await generate_text_to_speech(
            prompt=query_params.prompt, response_format=response_audio_file_format  # type: ignore
        )

    # try to guess the mimetype from the file path's extension if we don't already know it
    content_type: str | None = content_type or mimetypes.guess_type(query_params.file_path)[0]  # type: ignore

    # Upload the generated file to S3
    upload_s3_object(
        bucket_name=s3_bucket_name,
        object_key=query_params.file_path,
        file_content=file_content_bytes,
        content_type=content_type,
    )

    # return response
    response.status_code = status.HTTP_201_CREATED
    return PutGeneratedFileResponse(
        file_path=query_params.file_path,
        message=f"New {query_params.file_type.value} file generated and uploaded at path: {query_params.file_path}",
    )
