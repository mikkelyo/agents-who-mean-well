"""Base exception for every failure the API reports to a caller."""

from template_project.domain.enums.api_error_code import APIErrorCode


class APIException(Exception):
    """Domain failure identified by a stable error code."""

    def __init__(
        self,
        error_code: APIErrorCode = APIErrorCode.API_ERROR,
        detail: str = "An unexpected error occurred.",
    ) -> None:
        self.error_code = error_code
        self.detail = detail
        super().__init__(detail)
