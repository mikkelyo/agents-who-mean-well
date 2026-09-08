"""Machine-readable error codes returned to API clients."""

from enum import Enum


class APIErrorCode(str, Enum):
    """Stable error identifiers carried by every :class:`APIException`."""

    API_ERROR: str = "api/error"
    AUTHENTICATION_ERROR: str = "api/authentication-error"
    VALIDATION_ERROR: str = "api/validation-error"
