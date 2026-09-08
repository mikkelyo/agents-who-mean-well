"""Maps exceptions to the error DTO the API contract promises."""

from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Starlette raises its own HTTPException for unmatched routes; FastAPI's subclasses it,
# so handling the base class covers both.
from starlette.exceptions import HTTPException

from template_project.constants.static_messages import StaticMessages
from template_project.di_container import container
from template_project.domain.enums.api_error_code import APIErrorCode
from template_project.domain.exceptions.api_exception import APIException
from template_project.presentation.response_models.base.error_response_models import (
    ErrorResponse,
)

logger = container.infrastructure.logger()

# The only place that knows which HTTP status a domain failure is served as.
STATUS_BY_ERROR_CODE: dict[APIErrorCode, int] = {
    APIErrorCode.API_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    APIErrorCode.AUTHENTICATION_ERROR: status.HTTP_401_UNAUTHORIZED,
    APIErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
}


def _problem(
    status_code: int,
    detail: str,
    error_code: APIErrorCode,
    errors: list[str] | None = None,
) -> JSONResponse:
    """Render one failure as the shared error body."""
    body = ErrorResponse(
        type=f"https://httpstatuses.com/{status_code}",
        title=HTTPStatus(status_code).phrase,
        status=status_code,
        detail=detail,
        error_code=error_code.value,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(by_alias=True, exclude_none=True),
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Render a FastAPI payload validation failure as a 400."""
    return _problem(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=StaticMessages.INVALID_PAYLOAD,
        error_code=APIErrorCode.VALIDATION_ERROR,
        errors=[
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        ],
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Render any framework-raised HTTP error, keeping the status it carries."""
    return _problem(
        status_code=exc.status_code,
        detail=str(exc.detail),
        error_code=APIErrorCode.API_ERROR,
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Render any domain failure as the status its error code maps to."""
    return _problem(
        status_code=STATUS_BY_ERROR_CODE[exc.error_code],
        detail=exc.detail,
        error_code=exc.error_code,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render a failure nothing anticipated, so no caller ever sees a bare 500."""
    # Detail is deliberately generic: the traceback belongs in the log, not the body.
    logger.exception("Unhandled error serving %s %s.", request.method, request.url.path)
    return _problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=StaticMessages.UNEXPECTED_ERROR,
        error_code=APIErrorCode.API_ERROR,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler above to ``app``.

    ``APIException`` covers its subclasses: Starlette walks the exception's MRO
    when it looks a handler up. The ``Exception`` handler is the last resort;
    Starlette re-raises after it responds, so the failure still reaches the logs.
    """
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(APIException, api_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
