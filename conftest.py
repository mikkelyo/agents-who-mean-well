"""Test bootstrap: required environment must exist before ``config`` is imported."""

import os

os.environ.setdefault("APP_ENV_NAME", "test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-api-key")
os.environ.setdefault("SERVICE_API_KEY", "test-service-api-key")

import pytest  # noqa: E402


@pytest.fixture
def anyio_backend() -> str:
    """Run anyio-driven tests on asyncio."""
    return "asyncio"
