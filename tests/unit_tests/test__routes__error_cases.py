import pytest
from fastapi import status
from fastapi.testclient import TestClient

from files_api.schemas import DEFAULT_GET_FILES_MAX_PAGE_SIZE

INVALID_FILE_PATH = "files/file*.txt"


@pytest.mark.parametrize(
    "verb",
    ["get", "head", "delete"],
)
def test_nonexistent_files_endpoints(client: TestClient, verb: str):
    response = getattr(client, verb)("/files/nowhere/nothing.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    if verb != "head":
        assert response.json()["detail"] == "File not found."


def test_get_files_invalid_page_size(client: TestClient):
    response = client.get("/files?page_size=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.get(f"/files?page_size={DEFAULT_GET_FILES_MAX_PAGE_SIZE + 1}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "invalid_path",
    [
        "file*.txt",  # wildcard
        "file<name>.txt",  # angle brackets
        "file|name.txt",  # pipe
        'file"name.txt',  # quote
        "file:name.txt",  # colon
    ],
)
@pytest.mark.parametrize(
    "verb",
    ["get", "head", "delete"],
)
def test_get_file_invalid_filepath(client: TestClient, verb: str, invalid_path: str):
    """Test that invalid file paths are rejected."""
    response = getattr(client, verb)(f"/files/{invalid_path}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "invalid_path",
    [
        "file*.txt",  # wildcard
        "file<name>.txt",  # angle brackets
        "file|name.txt",  # pipe
        'file"name.txt',  # quote
        "file:name.txt",  # colon
    ],
)
def test_put_file_invalid_filepath(client: TestClient, invalid_path: str):
    """Test that invalid file paths are rejected for PUT requests."""
    response = client.put(
        f"/files/{invalid_path}",
        files={"file": ("test.txt", "test content", "text/plain")},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
