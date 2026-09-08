"""Raised when the caller cannot be identified."""

from agents_who_mean_well.domain.enums.api_error_code import APIErrorCode
from agents_who_mean_well.domain.exceptions.api_exception import APIException


class AuthenticationException(APIException):
    """The request carries no usable identity."""

    def __init__(self, detail: str = "The request is not authenticated.") -> None:
        super().__init__(error_code=APIErrorCode.AUTHENTICATION_ERROR, detail=detail)
