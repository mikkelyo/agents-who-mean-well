"""Bridges request-scoped identity into singleton infrastructure."""

from __future__ import annotations

from typing import TYPE_CHECKING

from template_project.constants.context_keys import ContextKeys
from template_project.constants.static_messages import StaticMessages
from template_project.context import context
from template_project.domain.exceptions.authentication_exception import (
    AuthenticationException,
)

if TYPE_CHECKING:
    from logging import Logger

    from template_project.domain.user.current_user import CurrentUser


class ContextVarCurrentUserAdapter:
    """Implements :class:`CurrentUserPort`, so use cases never touch HTTP state."""

    def __init__(self, *, logger: Logger) -> None:
        self._logger = logger

    def get_current_user(self) -> CurrentUser:
        """Return the caller bound to the current request context."""
        current_user: CurrentUser | None = context.get(ContextKeys.CURRENT_USER)
        if current_user is None:
            self._logger.warning(StaticMessages.MISSING_CURRENT_USER)
            raise AuthenticationException(detail=StaticMessages.MISSING_CURRENT_USER)
        return current_user
