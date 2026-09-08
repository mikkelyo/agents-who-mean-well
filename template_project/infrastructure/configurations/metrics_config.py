"""Configuration for operational metrics."""

from pydantic import BaseModel, Field

from template_project.infrastructure.configurations.base.env_string_validators import (
    EnvNameString,
)


class MetricsConfig(BaseModel):
    """How recorded metrics are named and whether they are emitted."""

    namespace: EnvNameString = Field(
        "{env_name}.template_project",
        validate_default=True,
        description="Prefix for every metric name.",
    )
    enabled: bool = Field(True, description="Whether metrics are recorded at all.")
