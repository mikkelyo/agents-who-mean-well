"""Configuration for inbound request authentication."""

from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """How callers of this service are authenticated."""

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"], description="Origins accepted by CORS."
    )
