"""Tests for the request-scoped current user adapter."""

from unittest.mock import MagicMock

import pytest

from template_project.application.ports.current_user_port import CurrentUserPort
from template_project.constants.context_keys import ContextKeys
from template_project.context import context
from template_project.domain.exceptions.authentication_exception import (
    AuthenticationException,
)
from template_project.domain.user.current_user import CurrentUser
from template_project.presentation.user.context_var_current_user_adapter import (
    ContextVarCurrentUserAdapter,
)


@pytest.fixture
def adapter() -> ContextVarCurrentUserAdapter:
    """Return the adapter under test."""
    return ContextVarCurrentUserAdapter(logger=MagicMock())


class TestGetCurrentUser:
    """Cases for :meth:`ContextVarCurrentUserAdapter.get_current_user`."""

    def test_satisfies_the_port(self, adapter: ContextVarCurrentUserAdapter) -> None:
        """Conformance is structural, so it needs asserting."""
        assert isinstance(adapter, CurrentUserPort)

    def test_returns_the_user_bound_to_the_context(
        self, adapter: ContextVarCurrentUserAdapter
    ) -> None:
        """The adapter reads whatever the auth dependency bound."""
        user = CurrentUser(user_id="u-1", user_name="Ada")
        context.set(ContextKeys.CURRENT_USER, user)

        assert adapter.get_current_user() == user

    def test_raises_when_nothing_is_bound(
        self, adapter: ContextVarCurrentUserAdapter
    ) -> None:
        """An unbound context means the request was never authenticated."""
        context.set(ContextKeys.CURRENT_USER, None)

        with pytest.raises(AuthenticationException):
            adapter.get_current_user()
