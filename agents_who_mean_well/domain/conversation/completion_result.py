"""Outcome of a completion request."""

from pydantic import BaseModel, Field


class CompletionResult(BaseModel):
    """What the model answered and who asked for it."""

    answer: str = Field(..., description="Text produced by the model.")
    requested_by: str = Field(
        ..., description="Identifier of the caller the answer was produced for."
    )
