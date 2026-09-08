"""Raised when a request payload is structurally valid but semantically wrong."""

from template_project.domain.enums.api_error_code import APIErrorCode
from template_project.domain.exceptions.api_exception import APIException


class ValidationException(APIException):
    """A value supplied by the caller is not acceptable."""

    def __init__(
        self,
        detail: str = "The request payload is invalid.",
        field: str | None = None,
    ) -> None:
        super().__init__(
            error_code=APIErrorCode.VALIDATION_ERROR,
            detail=f"{field}: {detail}" if field else detail,
        )
