"""Tests for the Anthropic-backed completion adapter."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from anthropic import AnthropicError
from pydantic import BaseModel

from template_project.application.ports.completion_port import CompletionPort
from template_project.domain.conversation.message import Message
from template_project.domain.enums.message_role import MessageRole
from template_project.domain.exceptions.api_exception import APIException
from template_project.domain.user.current_user import CurrentUser
from template_project.infrastructure.anthropic.anthropic_completion_adapter import (
    AnthropicCompletionAdapter,
)


class Answer(BaseModel):
    """Schema used to exercise structured completions."""

    value: int


@pytest.fixture
def client() -> MagicMock:
    """Return an SDK client that answers with a single text block."""
    sdk = MagicMock()
    sdk.messages.create = AsyncMock(
        return_value=SimpleNamespace(content=[SimpleNamespace(type="text", text="42")])
    )
    return sdk


@pytest.fixture
def adapter(client: MagicMock) -> AnthropicCompletionAdapter:
    """Return the adapter under test."""
    current_user = MagicMock()
    current_user.get_current_user.return_value = CurrentUser(
        user_id="u-1", user_name="Ada"
    )
    return AnthropicCompletionAdapter(
        client=client,
        logger=MagicMock(),
        current_user=current_user,
        model="claude-sonnet-4-6",
        max_tokens=16,
        temperature=0.0,
    )


class TestComplete:
    """Cases for :meth:`AnthropicCompletionAdapter.complete`."""

    def test_satisfies_the_port(self, adapter: AnthropicCompletionAdapter) -> None:
        """Conformance is structural, so it needs asserting."""
        assert isinstance(adapter, CompletionPort)

    async def test_converts_domain_turns_and_attributes_the_caller(
        self, adapter: AnthropicCompletionAdapter, client: MagicMock
    ) -> None:
        """Domain types are converted to the SDK payload at the boundary."""
        answer = await adapter.complete(
            messages=[Message(role=MessageRole.USER, content="Hi")], system="Be brief."
        )

        kwargs = client.messages.create.await_args.kwargs
        assert answer == "42"
        assert kwargs["messages"] == [{"role": "user", "content": "Hi"}]
        assert kwargs["metadata"] == {"user_id": "u-1"}

    async def test_translates_vendor_failures_into_domain_failures(
        self, adapter: AnthropicCompletionAdapter, client: MagicMock
    ) -> None:
        """SDK exceptions must not leak past the adapter."""
        client.messages.create.side_effect = AnthropicError("no credentials")

        with pytest.raises(APIException):
            await adapter.complete(
                messages=[Message(role=MessageRole.USER, content="Hi")], system=""
            )

    async def test_raises_when_the_model_returns_no_text(
        self, adapter: AnthropicCompletionAdapter, client: MagicMock
    ) -> None:
        """An answerless response is a server-side failure."""
        client.messages.create.return_value = SimpleNamespace(content=[])

        with pytest.raises(APIException):
            await adapter.complete(
                messages=[Message(role=MessageRole.USER, content="Hi")], system=""
            )


class TestCompleteStructured:
    """Cases for :meth:`AnthropicCompletionAdapter.complete_structured`."""

    async def test_forces_the_tool_call_and_validates_the_result(
        self, adapter: AnthropicCompletionAdapter, client: MagicMock
    ) -> None:
        """The schema is exposed as a tool the model is required to call."""
        client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="tool_use", input={"value": 42})]
        )

        result = await adapter.complete_structured(
            messages=[Message(role=MessageRole.USER, content="Hi")],
            schema=Answer,
            description="The answer.",
        )

        kwargs = client.messages.create.await_args.kwargs
        assert result == Answer(value=42)
        assert kwargs["tool_choice"] == {"type": "tool", "name": "Answer"}
        assert kwargs["tools"][0]["name"] == "Answer"
