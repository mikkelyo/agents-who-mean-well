"""Roles a conversation turn can be attributed to."""

from enum import Enum


class MessageRole(str, Enum):
    """Author of a conversation turn."""

    USER: str = "user"
    ASSISTANT: str = "assistant"
