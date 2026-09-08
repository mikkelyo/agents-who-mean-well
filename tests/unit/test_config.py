"""Tests for the settings composition root."""

from config import settings


class TestSettings:
    """Cases for the merged settings object."""

    def test_settings_file_overrides_pydantic_defaults(self) -> None:
        """Values in settings.json win over the model defaults."""
        assert settings.anthropic_config.model == "claude-sonnet-4-6"
        assert settings.anthropic_config.max_tokens == 4096
        assert settings.example_api_config.timeout_seconds == 10.0

    def test_environment_name_is_interpolated_into_scoped_values(self) -> None:
        """Environment-scoped names must never reach an adapter unresolved."""
        assert settings.app_env_name == "test"
        assert settings.example_api_config.base_url == "https://api.test.example.com"
        assert settings.metrics_config.namespace == "test.template_project"
