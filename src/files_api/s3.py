import boto3

BUCKET_NAME = "cloud-course-bucket-whalen"

session = boto3.Session(profile_name="cloud-course")

s3_client = session.client("s3")

response = s3_client.put_object(Bucket=BUCKET_NAME, Key="hello.txt", Body="Hello, World!", ContentType="text/plain")
