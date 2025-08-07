import boto3
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .storage import get_storage


def generate_presigned_url(key, expires_in=3600):
    """Return an accessible URL for a stored file.

    When using the local filesystem storage backend (typically in development)
    a regular media URL is returned as signed URLs are unnecessary. In other
    environments the function falls back to generating an AWS S3 presigned URL
    so that private objects can be retrieved securely.
    """

    storage = get_storage()
    if isinstance(storage, FileSystemStorage):
        return storage.url(key)

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
