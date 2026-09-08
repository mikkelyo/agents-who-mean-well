"""Port exposing text and structured completions from a language model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Sequence

    from template_project.domain.conversation.message import Message

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@runtime_checkable
class CompletionPort(Protocol):
    """Hides which vendor backs the model, how it is authenticated and called."""

    async def complete(self, *, messages: Sequence[Message], system: str) -> str:
        """Answer a conversation with free-form text."""
        ...

    async def complete_structured(
        self,
        *,
        messages: Sequence[Message],
        schema: type[SchemaT],
        description: str,
    ) -> SchemaT:
        """Answer a conversation with an instance of ``schema``."""
        ...
