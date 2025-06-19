import boto3

from files_api.s3.delete_objects import delete_s3_object
from files_api.s3.read_objects import object_exists_in_s3
from files_api.s3.write_objects import upload_s3_object
from tests.consts import TEST_BUCKET_NAME


def test_delete_existing_s3_object(mocked_aws: None):
    test_key = "test.txt"

    upload_s3_object(TEST_BUCKET_NAME, test_key, b"test")

    assert object_exists_in_s3(TEST_BUCKET_NAME, test_key)

    delete_s3_object(TEST_BUCKET_NAME, test_key)

    assert not object_exists_in_s3(TEST_BUCKET_NAME, test_key)


def test_delete_nonexistent_s3_object(mocked_aws: None):
    test_key = "test.txt"

    assert not object_exists_in_s3(TEST_BUCKET_NAME, test_key)

    delete_s3_object(TEST_BUCKET_NAME, test_key)
