import os
import boto3
from dotenv import load_dotenv

load_dotenv()

bucket = os.getenv("S3_BUCKET_NAME")
region = os.getenv("AWS_REGION")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=region
)

test_content = b"hackathon test upload"
s3.put_object(Bucket=bucket, Key="test/connection_check.txt", Body=test_content)
print("Upload succeeded.")

response = s3.get_object(Bucket=bucket, Key="test/connection_check.txt")
print("Read back:", response["Body"].read().decode())