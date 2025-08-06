from enum import IntEnum

from ninja.errors import HttpError


class APIError(HttpError):
    """Generic API error containing a numeric error code."""

    def __init__(self, message: str, code: IntEnum, status_code: int = 400):
        super().__init__(status_code, message)
        self.message = message
        self.code = code

    def __str__(self) -> str:  # pragma: no cover - simple string repr
        return f"[{int(self.code)}] {self.message}"


class ReservationErrorCode(IntEnum):
    """Error codes for reservation related issues."""

    UNKNOWN_ERROR = 100
    NO_AVAILABILITY = 101
    INVALID_DATES = 102
    PAYMENT_FAILED = 103
    NOT_FOUND = 104
    CANCEL_NOT_ALLOWED = 105


class ReservationError(APIError):
    """HttpError subclass that carries a ReservationErrorCode."""

    def __init__(
        self, message: str, code: ReservationErrorCode, status_code: int = 400
    ):
        super().__init__(message, code, status_code)


class PropertyErrorCode(IntEnum):
    """Error codes for property related issues."""

    INVALID_CHECKIN_DATE = 200
    CHECKIN_AFTER_CHECKOUT = 201
    PROPERTY_NOT_FOUND = 202
    RATES_PARSE_ERROR = 203
    PRICE_NOT_FOUND = 204
    NO_AVAILABILITY = 205
    ROOM_TYPE_NOT_FOUND = 206
    ZONE_OR_PROPERTY_REQUIRED = 207
    SERVICE_NOT_FOUND = 208


class CustomerErrorCode(IntEnum):
    """Error codes for customer related issues."""

    EMAIL_EXISTS = 300
    USER_INACTIVE = 301
    INVALID_CREDENTIALS = 302
    USER_NOT_FOUND = 303
    UNAUTHENTICATED = 304
    REFRESH_TOKEN_INVALID = 305
    TOKEN_INVALID = 306


class SecurityErrorCode(IntEnum):
    """Error codes for security related issues."""

    ACCESS_DENIED = 400


class ZoneErrorCode(IntEnum):
    """Error codes for zone related issues."""

    ZONE_NOT_FOUND = 500
    INVALID_ZONE_ID = 501
    ZONE_AREA_TOO_LARGE = 502
