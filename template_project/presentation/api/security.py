"""Authentication dependencies and the composed dependency lists routes apply."""

from json import JSONDecodeError

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from template_project.constants.context_keys import ContextKeys
from template_project.constants.static_messages import StaticMessages
from template_project.context import context
from template_project.domain.exceptions.authentication_exception import (
    AuthenticationException,
)
from template_project.domain.exceptions.validation_exception import ValidationException
from template_project.domain.user.current_user import CurrentUser

bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Reject requests that do not carry the configured bearer token."""
    if credentials is None or credentials.credentials != settings.service_api_key:
        raise AuthenticationException(detail=StaticMessages.INVALID_API_KEY)


async def set_current_user_from_body(request: Request) -> None:
    """Bind the caller described in the request body to the request context."""
    # This runs before FastAPI parses the body into a DTO, so a body that is not a
    # JSON object would otherwise escape the error contract as a 500.
    try:
        body = await request.json()
    except JSONDecodeError as error:
        raise ValidationException(detail=StaticMessages.INVALID_PAYLOAD) from error
    if not isinstance(body, dict):
        raise ValidationException(detail=StaticMessages.INVALID_PAYLOAD)

    user_id = body.get("UserId")
    user_name = body.get("UserName")
    if not user_id or not user_name:
        raise AuthenticationException(detail=StaticMessages.MISSING_CURRENT_USER)
    context.set(
        ContextKeys.CURRENT_USER,
        CurrentUser(user_id=user_id, user_name=user_name),
    )


# Routes without a request body: reading one would fail before the handler runs.
AUTH_ONLY = [Depends(require_api_key)]

# Routes whose body carries the caller.
AUTH_AND_CONTEXT = [*AUTH_ONLY, Depends(set_current_user_from_body)]
