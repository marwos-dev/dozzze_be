# security.py
from ninja.security import APIKeyHeader
from django.conf import settings
from ninja.errors import HttpError

class PublicAPIKey(APIKeyHeader):
    param_name = "X-APP-KEY"

    def authenticate(self, request, key):
        if settings.DEVELOPMENT:
            # In development mode, allow any key
            return True

        if key == settings.PUBLIC_API_KEY:
            return key
        raise HttpError(403, "Access denied")

