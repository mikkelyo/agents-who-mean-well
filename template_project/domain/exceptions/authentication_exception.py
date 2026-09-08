"""Raised when the caller cannot be identified."""

from template_project.domain.enums.api_error_code import APIErrorCode
from template_project.domain.exceptions.api_exception import APIException


class AuthenticationException(APIException):
    """The request carries no usable identity."""

    def __init__(self, detail: str = "The request is not authenticated.") -> None:
        super().__init__(error_code=APIErrorCode.AUTHENTICATION_ERROR, detail=detail)
