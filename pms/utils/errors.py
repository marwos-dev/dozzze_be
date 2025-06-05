from requests import HTTPError


class PmsError(HTTPError):
    """
    Base error class.

    Subclassing HTTPError to avoid breaking existing code that expects only HTTPErrors.
    """


class PmsBadRequest(PmsError):
    """Most 40X and 501 status codes"""


class PmsUnauthorized(PmsError):
    """401 Unauthorized"""


class PmsAccessDenied(PmsError):
    """403 Forbidden"""


class PmsNotFound(PmsError):
    """404"""


class PmsRateLimited(PmsError):
    """429 Rate Limit Reached"""


class PmsServerError(PmsError):
    """50X errors"""
