"""Raised when a request payload is structurally valid but semantically wrong."""

from agents_who_mean_well.domain.enums.api_error_code import APIErrorCode
from agents_who_mean_well.domain.exceptions.api_exception import APIException


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
