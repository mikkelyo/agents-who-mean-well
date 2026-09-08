"""A single turn in a conversation with a language model."""

from pydantic import BaseModel, Field

from template_project.domain.enums.message_role import MessageRole


class Message(BaseModel):
    """One conversation turn, independent of any model vendor."""

    role: MessageRole = Field(..., description="Who produced the turn.")
    content: str = Field(..., description="Text of the turn.")
