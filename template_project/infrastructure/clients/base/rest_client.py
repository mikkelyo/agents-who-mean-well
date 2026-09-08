"""Async HTTP client shared by every outbound REST integration."""

from typing import Any

import httpx


class RestClient:
    """Thin async wrapper over :class:`httpx.AsyncClient`."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        default_headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_headers = default_headers or {}
        self._client = client or httpx.AsyncClient(timeout=timeout)

    def _build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return f"{self._base_url}/{path.lstrip('/')}"

    def _authorized_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        merged = dict(self._default_headers)
        if self._api_key:
            merged["Authorization"] = f"Bearer {self._api_key}"
        merged.update(headers or {})
        return merged

    async def request(
        self,
        *,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        auto_raise: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a request, raising on 4xx/5xx unless ``auto_raise`` is off."""
        response = await self._client.request(
            method,
            self._build_url(path),
            headers=self._authorized_headers(headers),
            **kwargs,
        )
        if auto_raise:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                # httpx omits the body, which is where APIs explain the failure.
                raise httpx.HTTPStatusError(
                    f"{error}. Response body: {response.text}",
                    request=error.request,
                    response=error.response,
                ) from error
        return response

    async def get(self, *, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request(method="GET", path=path, **kwargs)

    async def post(self, *, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request(method="POST", path=path, **kwargs)

    async def put(self, *, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request(method="PUT", path=path, **kwargs)

    async def delete(self, *, path: str, **kwargs: Any) -> httpx.Response:
        return await self.request(method="DELETE", path=path, **kwargs)

    async def aclose(self) -> None:
        await self._client.aclose()
