"""Port exposing the caller behind the in-flight request."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from template_project.domain.user.current_user import CurrentUser


@runtime_checkable
class CurrentUserPort(Protocol):
    """Hides where the identity comes from — HTTP headers, a body field or a token."""

    def get_current_user(self) -> CurrentUser:
        """Return the caller the current request runs on behalf of."""
        ...
