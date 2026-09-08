"""Anthropic-backed implementation of the completion port."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from anthropic import AnthropicError, AsyncAnthropic
from anthropic.types import MessageParam, MetadataParam, ToolChoiceToolParam, ToolParam
from pydantic import BaseModel

from template_project.constants.static_messages import StaticMessages
from template_project.domain.enums.message_role import MessageRole
from template_project.domain.exceptions.api_exception import APIException

if TYPE_CHECKING:
    from collections.abc import Sequence
    from logging import Logger

    from template_project.application.ports.current_user_port import CurrentUserPort
    from template_project.domain.conversation.message import Message

SchemaT = TypeVar("SchemaT", bound=BaseModel)

# Roles are translated explicitly, so a new domain role cannot silently reach the SDK.
VENDOR_ROLES: dict[MessageRole, Literal["user", "assistant"]] = {
    MessageRole.USER: "user",
    MessageRole.ASSISTANT: "assistant",
}


class AnthropicCompletionAdapter:
    """Implements :class:`CompletionPort`, so the Anthropic SDK stays in this layer."""

    def __init__(
        self,
        *,
        client: AsyncAnthropic,
        logger: Logger,
        current_user: CurrentUserPort,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> None:
        self._client = client
        self._logger = logger
        self._current_user = current_user
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def complete(self, *, messages: Sequence[Message], system: str) -> str:
        """Answer a conversation with free-form text."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                system=system,
                messages=self._to_vendor_messages(messages),
                metadata=self._caller_metadata(),
            )
        except AnthropicError as error:
            self._logger.error("Anthropic rejected the completion: %s", error)
            raise APIException(detail=StaticMessages.COMPLETION_FAILED) from error
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            self._logger.error("Anthropic returned no text block for %s.", self._model)
            raise APIException(detail=StaticMessages.COMPLETION_FAILED)
        return text

    async def complete_structured(
        self,
        *,
        messages: Sequence[Message],
        schema: type[SchemaT],
        description: str,
    ) -> SchemaT:
        """Answer a conversation with an instance of ``schema``."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                messages=self._to_vendor_messages(messages),
                tools=[self._to_vendor_tool(schema=schema, description=description)],
                tool_choice=ToolChoiceToolParam(type="tool", name=schema.__name__),
                metadata=self._caller_metadata(),
            )
        except AnthropicError as error:
            self._logger.error("Anthropic rejected the tool call: %s", error)
            raise APIException(detail=StaticMessages.COMPLETION_FAILED) from error
        block = next((b for b in response.content if b.type == "tool_use"), None)
        if block is None:
            self._logger.error(
                "Anthropic returned no tool call for %s.", schema.__name__
            )
            raise APIException(detail=StaticMessages.COMPLETION_FAILED)
        return schema.model_validate(block.input)

    def _caller_metadata(self) -> MetadataParam:
        """Attribute the call to the current caller."""
        return MetadataParam(user_id=self._current_user.get_current_user().user_id)

    @staticmethod
    def _to_vendor_messages(messages: Sequence[Message]) -> list[MessageParam]:
        """Convert domain turns into the SDK's message payload."""
        return [
            MessageParam(role=VENDOR_ROLES[m.role], content=m.content) for m in messages
        ]

    @staticmethod
    def _to_vendor_tool(*, schema: type[BaseModel], description: str) -> ToolParam:
        """Expose ``schema`` as a tool definition the model must call."""
        return ToolParam(
            name=schema.__name__,
            description=description,
            input_schema=schema.model_json_schema(),
        )
