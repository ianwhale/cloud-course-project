"""Test fastapi app."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from files_api.s3.write_objects import upload_s3_object
from files_api.schemas import GeneratedFileType
from tests.consts import TEST_BUCKET_NAME

TEST_FILE_PATH = "some/nested/file.txt"
TEST_FILE_CONTENT = b"test"
TEST_FILE_CONTENT_TYPE = "text/plain"


def test_upload_file(client: TestClient):
    response = client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={
            "file_content": (TEST_FILE_PATH, TEST_FILE_CONTENT, TEST_FILE_CONTENT_TYPE)
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {
        "file_path": TEST_FILE_PATH,
        "message": f"New file uploaded at path: /{TEST_FILE_PATH}",
    }

    updated_content = b"new content"
    response = client.put(
        f"/v1/files/{TEST_FILE_PATH}",
        files={
            "file_content": (TEST_FILE_PATH, updated_content, TEST_FILE_CONTENT_TYPE)
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "file_path": TEST_FILE_PATH,
        "message": f"Existing file updated at path: /{TEST_FILE_PATH}",
    }


@pytest.mark.xfail(reason="Currently a bug in pagination mutual exclusivity condition.")
def test_list_files_with_pagination(client: TestClient):
    for i in range(1, 12):
        upload_s3_object(
            bucket_name=TEST_BUCKET_NAME,
            object_key=f"file_{i}.txt",
            file_content=b"blah_" + f"{i}".encode(),
        )

    # Get everything without pagination first.
    response = client.get("/v1/files?page_size=100")

    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["files"]) == 11
    assert response_json["next_page_token"] is None
    assert response_json["files"][0]["file_path"] == "file_1.txt"

    response = client.get("/v1/files?page_size=10")

    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["files"]) == 10
    assert isinstance(response_json["next_page_token"], str)

    response = client.get(f"/v1/files?page_token={response_json['next_page_token']}")

    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["files"]) == 1
    assert response_json["next_page_token"] is None


def test_get_file_metadata(client: TestClient):
    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=TEST_FILE_PATH,
        file_content=TEST_FILE_CONTENT,
        content_type=TEST_FILE_CONTENT_TYPE,
    )

    response = client.head(f"/v1/files/{TEST_FILE_PATH}")

    assert response.status_code == status.HTTP_200_OK

    headers = response.headers
    assert headers["Content-Type"] == TEST_FILE_CONTENT_TYPE
    assert headers["Content-Length"] == str(len(TEST_FILE_CONTENT))
    assert "Last-Modified" in headers


def test_get_file(client: TestClient):
    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=TEST_FILE_PATH,
        file_content=TEST_FILE_CONTENT,
        content_type=TEST_FILE_CONTENT_TYPE,
    )

    response = client.get(f"/v1/files/{TEST_FILE_PATH}")

    assert response.status_code == status.HTTP_200_OK
    assert response.content == TEST_FILE_CONTENT


def test_delete_file(client: TestClient):
    upload_s3_object(
        bucket_name=TEST_BUCKET_NAME,
        object_key=TEST_FILE_PATH,
        file_content=TEST_FILE_CONTENT,
        content_type=TEST_FILE_CONTENT_TYPE,
    )

    response = client.delete(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_generate_text(client: TestClient):
    """Test generating text using POST method."""
    response = client.post(
        url=f"/v1/files/generated/{TEST_FILE_PATH}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.TEXT.value},
    )

    respone_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        respone_data["message"]
        == f"New {GeneratedFileType.TEXT.value} file generated and uploaded at path: {TEST_FILE_PATH}"
    )

    # Get the generated file
    response = client.get(f"/v1/files/{TEST_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.content
        == b"This is a mock response from the chat completion endpoint."
    )
    assert "text/plain" in response.headers["Content-Type"]


def test_generate_image(client: TestClient):
    """Test generating image using POST method."""
    IMAGE_FILE_PATH = "some/nested/path/image.png"  # pylint: disable=invalid-name
    response = client.post(
        url=f"/v1/files/generated/{IMAGE_FILE_PATH}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.IMAGE.value},
    )

    respone_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        respone_data["message"]
        == f"New {GeneratedFileType.IMAGE.value} file generated and uploaded at path: {IMAGE_FILE_PATH}"
    )

    # Get the generated file
    response = client.get(f"/v1/files/{IMAGE_FILE_PATH}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content is not None
    assert response.headers["Content-Type"] == "image/png"


def test_generate_audio(client: TestClient):
    """Test generating an audio file using the POST method."""
    audio_file_path = "some-audio.mp3"
    response = client.post(
        url=f"/v1/files/generated/{audio_file_path}",
        params={"prompt": "Test Prompt", "file_type": GeneratedFileType.AUDIO.value},
    )

    response_data = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["message"] == (
        f"New text-to-speech file generated and uploaded at path: {audio_file_path}"
    )

    # Get the generated file
    response = client.get(f"/v1/files/{audio_file_path}")
    assert response.status_code == status.HTTP_200_OK
    assert response.content is not None
    assert response.headers["Content-Type"] == "audio/mpeg"
