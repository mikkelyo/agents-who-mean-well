"""The single outbound DTO describing a failure, shaped after RFC 7807."""

from pydantic import Field

from template_project.presentation.response_models.base.base_response_model import (
    BaseResponseModel,
)


class ErrorResponse(BaseResponseModel):
    """Body of every error response, whatever the status."""

    type: str = Field(..., alias="Type", description="URI describing the status.")
    title: str = Field(..., alias="Title", description="Short summary.")
    status: int = Field(..., alias="Status", description="HTTP status code.")
    detail: str = Field(..., alias="Detail", description="What went wrong.")
    error_code: str = Field(..., alias="ErrorCode", description="Error identifier.")
    errors: list[str] | None = Field(
        None, alias="Errors", description="Individual failures, when there are several."
    )
