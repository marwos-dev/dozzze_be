# flake8: noqa
from dotenv import load_dotenv

from .base import *  # noqa: F401,F403

load_dotenv(BASE_DIR / ".env.dev")

DEBUG = True
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use local storage for media files during development
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
