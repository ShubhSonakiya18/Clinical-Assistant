import boto3
from botocore.config import Config
from app.config import settings


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def generate_upload_url(storage_key: str, content_type: str = "audio/webm") -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": storage_key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )


def generate_download_url(storage_key: str) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": storage_key},
        ExpiresIn=3600,
    )


def get_audio_bytes(storage_key: str) -> bytes:
    client = get_r2_client()
    response = client.get_object(Bucket=settings.R2_BUCKET_NAME, Key=storage_key)
    return response["Body"].read()


def upload_bytes(storage_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    client = get_r2_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=storage_key,
        Body=data,
        ContentType=content_type,
    )
