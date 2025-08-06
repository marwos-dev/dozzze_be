# flake8: noqa
import os

from dotenv import load_dotenv

from .base import *  # noqa: F401,F403

load_dotenv(BASE_DIR / ".env")  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = (
    os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else []
)
