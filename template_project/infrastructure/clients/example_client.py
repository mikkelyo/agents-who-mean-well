"""HTTP client for the example downstream API."""

from typing import Any

from template_project.infrastructure.clients.base.rest_client import RestClient
from template_project.infrastructure.configurations.example_api_config import (
    ExampleApiConfig,
)


class ExampleClient(RestClient):
    """Calls the example downstream API and returns plain Python data."""

    async def fetch_item(self, *, item_id: str) -> dict[str, Any]:
        """Read a single item."""
        response = await self.get(path=f"/items/{item_id}")
        item: dict[str, Any] = response.json()
        return item


def create_example_client(*, config: ExampleApiConfig) -> ExampleClient:
    """Build an :class:`ExampleClient` from its configuration."""
    return ExampleClient(base_url=config.base_url, timeout=config.timeout_seconds)
