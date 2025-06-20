"""Test fastapi app."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.files_api.main import APP


# Fixture for FastAPI test client
@pytest.fixture
def client(mocked_aws) -> TestClient:  # pylint: disable=unused-argument
    with TestClient(APP) as client:
        yield client


def test_upload_file(client: TestClient):
    test_file_path = "some/nested/file.txt"
    test_file_content = b"sdlfkjada"
    test_file_content_type = "text/plain"

    response = client.put(
        f"/files/{test_file_path}",
        files={"file": (test_file_path, test_file_content, test_file_content_type)},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "file_path": test_file_path,
        "message": f"New file uploaded at path: /{test_file_path}",
    }

    updated_content = b"new content"
    response = client.put(
        f"/files/{test_file_path}",
        files={"file": (test_file_path, updated_content, test_file_content_type)},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "file_path": test_file_path,
        "message": f"Existing file updated at path: /{test_file_path}",
    }


def test_list_files_with_pagination(client: TestClient): ...


def test_get_file_metadata(client: TestClient): ...


def test_get_file(client: TestClient): ...


def test_delete_file(client: TestClient): ...
