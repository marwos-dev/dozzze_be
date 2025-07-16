# security.py
from django.conf import settings
from ninja.security import APIKeyHeader
from utils import APIError, SecurityErrorCode


class PublicAPIKey(APIKeyHeader):
    param_name = "X-APP-KEY"

    def authenticate(self, request, key):
        if settings.DEVELOPMENT:
            # In development mode, allow any key
            return True

        if key == settings.PUBLIC_API_KEY:
            return key
        raise APIError("Access denied", SecurityErrorCode.ACCESS_DENIED, 403)
