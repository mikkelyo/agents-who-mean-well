"""Composition root for configuration.

Pydantic models define the shape and defaults; Dynaconf layers ``settings.json``
and ``.secrets.json`` (and the environment) on top; the merged result is
re-validated through Pydantic so every layer reads typed config objects.
"""

from dynaconf import Dynaconf
from pydantic import BaseModel, Field

from template_project.application.configurations.completion_config import (
    CompletionConfig,
)
from template_project.domain.enums.environment import Environment
from template_project.infrastructure.configurations.anthropic_config import (
    AnthropicConfig,
)
from template_project.infrastructure.configurations.example_api_config import (
    ExampleApiConfig,
)
from template_project.infrastructure.configurations.metrics_config import MetricsConfig
from template_project.infrastructure.configurations.security_config import (
    SecurityConfig,
)


class Settings(BaseModel):
    """Every value the process needs, grouped by the system it configures."""

    # Use cases
    completion_config: CompletionConfig = CompletionConfig()

    # Infrastructure services
    anthropic_config: AnthropicConfig = AnthropicConfig()
    metrics_config: MetricsConfig = MetricsConfig()
    security_config: SecurityConfig = SecurityConfig()

    # External clients
    example_api_config: ExampleApiConfig = ExampleApiConfig()

    # General
    version: str = Field("1.0.0", description="Version reported by the API.")
    is_local: bool = Field(True, description="Whether this is a developer machine.")
    log_level: str = Field("INFO", description="Minimum level written to stdout.")
    app_env_name: str = Field(
        Environment.LOCAL.value, description="Deployment environment name."
    )

    # Secrets
    anthropic_api_key: str = Field(..., description="Credential for the Anthropic API.")
    service_api_key: str = Field(..., description="Token callers must present.")


dynaconf = Dynaconf(
    envvar_prefix=False,
    load_dotenv=True,
    settings_files=["./settings.json", "./.secrets.json"],
)

dynaconf_dict = {key.lower(): value for key, value in dict(dynaconf).items()}

settings: Settings = Settings(**dynaconf_dict)
