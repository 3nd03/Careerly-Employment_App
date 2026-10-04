import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

def upload_cv(file_bytes, profile_id, filename):
    s3 = get_s3_client()
    key = f"cvs/{profile_id}/{filename}"
    s3.put_object(Bucket=os.getenv("S3_BUCKET_NAME"), Key=key, Body=file_bytes)
    return key

def get_cv(key):
    s3 = get_s3_client()
    response = s3.get_object(Bucket=os.getenv("S3_BUCKET_NAME"), Key=key)
    return response["Body"].read()

def upload_avatar(file_bytes, user_id, filename):
    s3 = get_s3_client()
    key = f"avatars/{user_id}/{filename}"
    s3.put_object(Bucket=os.getenv("S3_BUCKET_NAME"), Key=key, Body=file_bytes)
    return key

def get_avatar_url(key, expires_in=3600):
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": os.getenv("S3_BUCKET_NAME"), "Key": key},
        ExpiresIn=expires_in,
    )

def delete_objects(keys):
    if not keys:
        return
    s3 = get_s3_client()
    s3.delete_objects(
        Bucket=os.getenv("S3_BUCKET_NAME"),
        Delete={"Objects": [{"Key": key} for key in keys]},
    )