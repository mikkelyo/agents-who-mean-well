"""Configuration for the completion use case."""

from pydantic import BaseModel, Field


class CompletionConfig(BaseModel):
    """Behaviour of the completion use case, whichever model backs it."""

    system_prompt: str = Field(
        "You are a helpful assistant.",
        description="Instructions prepended to every conversation.",
    )
