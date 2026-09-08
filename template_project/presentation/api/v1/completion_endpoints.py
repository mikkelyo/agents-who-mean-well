"""Routes exposing the completion use case."""

from fastapi import APIRouter

from template_project.di_container import container
from template_project.presentation.api.security import AUTH_AND_CONTEXT
from template_project.presentation.api.v1.error_responses import ERROR_RESPONSES
from template_project.presentation.request_models.completion_request_model import (
    CompletionRequestModel,
)
from template_project.presentation.response_models.completion_response_model import (
    CompletionResponseModel,
)

router = APIRouter(tags=["completions"])


@router.post(
    "/completions",
    response_model=CompletionResponseModel,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
    dependencies=AUTH_AND_CONTEXT,
)
async def create_completion(
    request_model: CompletionRequestModel,
) -> CompletionResponseModel:
    """Answer the caller's prompt with the language model."""
    completion_service = container.services.completion_service()
    result = await completion_service.complete(prompt=request_model.prompt)
    return CompletionResponseModel(
        answer=result.answer, requested_by=result.requested_by
    )
