"""Bridges request-scoped identity into singleton infrastructure."""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents_who_mean_well.constants.context_keys import ContextKeys
from agents_who_mean_well.constants.static_messages import StaticMessages
from agents_who_mean_well.context import context
from agents_who_mean_well.domain.exceptions.authentication_exception import (
    AuthenticationException,
)

if TYPE_CHECKING:
    from logging import Logger

    from agents_who_mean_well.domain.user.current_user import CurrentUser


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
