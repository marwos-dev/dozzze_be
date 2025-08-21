from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


def get_storage():
    """Return appropriate storage backend depending on environment.

    Uses local filesystem storage when DEBUG is True and S3 storage in
    production. This avoids unnecessary S3 requests during development.
    """
    return FileSystemStorage() if settings.DEBUG else S3Boto3Storage()
