"""Define testing utility functions."""

import boto3


def delete_s3_bucket(bucket_name: str) -> None:
    """Delete bucket and all objects inside."""
    s3_client = boto3.resource("s3")

    bucket = s3_client.Bucket(bucket_name)
    bucket.objects.all().delete()

    bucket.delete()
