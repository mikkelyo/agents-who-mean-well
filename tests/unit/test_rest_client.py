"""Tests for the shared async REST client."""

import httpx
import pytest

from template_project.infrastructure.clients.base.rest_client import RestClient


def _client(handler) -> RestClient:
    """Return a client whose transport is driven by ``handler``."""
    return RestClient(
        base_url="https://api.example.com/",
        api_key="secret",
        default_headers={"X-Source": "tests"},
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


class TestRequest:
    """Cases for :meth:`RestClient.request`."""

    async def test_resolves_paths_against_the_base_url(self) -> None:
        """A relative path is joined to the base URL exactly once."""
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(str(request.url))
            return httpx.Response(200, json={})

        await _client(handler).get(path="/items/1")

        assert seen == ["https://api.example.com/items/1"]

    async def test_merges_default_headers_and_the_bearer_token(self) -> None:
        """Per-call headers win over the defaults."""
        seen: list[httpx.Headers] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers)
            return httpx.Response(200, json={})

        await _client(handler).get(path="/items/1", headers={"X-Source": "override"})

        assert seen[0]["authorization"] == "Bearer secret"
        assert seen[0]["x-source"] == "override"

    async def test_raises_with_the_response_body_attached(self) -> None:
        """httpx omits the body, which is where APIs explain the failure."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, text="item is unknown")

        with pytest.raises(httpx.HTTPStatusError, match="item is unknown"):
            await _client(handler).get(path="/items/1")

    async def test_returns_error_responses_when_auto_raise_is_off(self) -> None:
        """Callers that handle statuses themselves opt out of raising."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="missing")

        response = await _client(handler).get(path="/items/1", auto_raise=False)

        assert response.status_code == 404
