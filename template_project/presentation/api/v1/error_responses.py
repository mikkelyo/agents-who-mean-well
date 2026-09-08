"""OpenAPI error schemas shared by every v1 route."""

from typing import Any

from template_project.presentation.response_models.base.error_response_models import (
    ErrorResponse,
)

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid request payload."},
    401: {"model": ErrorResponse, "description": "Unauthenticated caller."},
    500: {"model": ErrorResponse, "description": "Unexpected server failure."},
}
