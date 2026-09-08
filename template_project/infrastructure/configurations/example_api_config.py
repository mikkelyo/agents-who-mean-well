"""Configuration for the example downstream REST API."""

from pydantic import BaseModel, Field

from template_project.infrastructure.configurations.base.env_string_validators import (
    EnvNameString,
)


class ExampleApiConfig(BaseModel):
    """Connection settings for the downstream API the service calls."""

    base_url: EnvNameString = Field(
        "https://api.{env_name}.example.com",
        validate_default=True,
        description="Root URL of the API.",
    )
    timeout_seconds: float = Field(
        10.0, gt=0.0, le=120.0, description="Per-request timeout in seconds."
    )
