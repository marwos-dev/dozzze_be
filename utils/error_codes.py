from enum import IntEnum
from ninja.errors import HttpError


class ReservationErrorCode(IntEnum):
    """Error codes for reservation related issues."""

    UNKNOWN_ERROR = 100
    NO_AVAILABILITY = 101
    INVALID_DATES = 102
    PAYMENT_FAILED = 103
    NOT_FOUND = 104


class ReservationError(HttpError):
    """HttpError subclass that carries a ReservationErrorCode."""

    def __init__(self, message: str, code: ReservationErrorCode, status_code: int = 400):
        super().__init__(status_code, message)
        self.message = message
        self.code = code

    def __str__(self) -> str:  # pragma: no cover - simple string repr
        return f"[{self.code}] {self.message}"
