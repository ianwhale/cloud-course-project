import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "verb",
    ["get", "head", "delete"],
)
def test_nonexistent_files_endpoints(client: TestClient, verb: str):
    response = getattr(client, verb)("/files/nowhere/nothing.txt")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    if verb != "head":
        assert response.json()["detail"] == "File not found."
