"""Tests for the completion use case."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from template_project.application.completion_service import CompletionService
from template_project.domain.enums.message_role import MessageRole
from template_project.domain.exceptions.validation_exception import ValidationException
from template_project.domain.user.current_user import CurrentUser


@pytest.fixture
def completion() -> MagicMock:
    """Return a language model that answers with a fixed string."""
    port = MagicMock()
    port.complete = AsyncMock(return_value="42")
    return port


@pytest.fixture
def current_user() -> MagicMock:
    """Return a caller resolver bound to a known user."""
    port = MagicMock()
    port.get_current_user.return_value = CurrentUser(user_id="u-1", user_name="Ada")
    return port


@pytest.fixture
def metrics() -> MagicMock:
    """Return a metrics recorder that records nothing."""
    return MagicMock()


@pytest.fixture
def service(
    completion: MagicMock, current_user: MagicMock, metrics: MagicMock
) -> CompletionService:
    """Return the use case under test."""
    return CompletionService(
        logger=MagicMock(),
        completion=completion,
        current_user=current_user,
        metrics=metrics,
        system_prompt="You are a helpful assistant.",
    )


class TestComplete:
    """Cases for :meth:`CompletionService.complete`."""

    async def test_returns_the_models_answer_for_the_current_user(
        self, service: CompletionService
    ) -> None:
        """The answer is attributed to the caller resolved from the port."""
        result = await service.complete(prompt="What is six times seven?")

        assert result.answer == "42"
        assert result.requested_by == "u-1"

    async def test_sends_the_prompt_as_a_user_turn_with_the_system_prompt(
        self, service: CompletionService, completion: MagicMock
    ) -> None:
        """The prompt reaches the port as a single user message."""
        await service.complete(prompt="Hello")

        kwargs = completion.complete.await_args.kwargs
        assert kwargs["system"] == "You are a helpful assistant."
        assert [(m.role, m.content) for m in kwargs["messages"]] == [
            (MessageRole.USER, "Hello")
        ]

    async def test_records_a_counter_and_a_duration(
        self, service: CompletionService, metrics: MagicMock
    ) -> None:
        """Every served prompt is measured."""
        await service.complete(prompt="Hello")

        metrics.increment.assert_called_once_with(name="completion.requested")
        assert metrics.record_duration.call_args.kwargs["name"] == "completion.duration"

    async def test_rejects_a_blank_prompt_before_calling_the_model(
        self, service: CompletionService, completion: MagicMock
    ) -> None:
        """A blank prompt is a caller error, not a model call."""
        with pytest.raises(ValidationException):
            await service.complete(prompt="   ")

        completion.complete.assert_not_awaited()
