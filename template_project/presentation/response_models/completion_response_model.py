"""Outbound DTO for the completion endpoint."""

from pydantic import Field

from template_project.presentation.response_models.base.base_response_model import (
    BaseResponseModel,
)


class CompletionResponseModel(BaseResponseModel):
    """Body of a successful ``POST /v1/completions``."""

    answer: str = Field(..., alias="Answer", description="Text produced by the model.")
    requested_by: str = Field(
        ..., alias="RequestedBy", description="Caller the answer was produced for."
    )
