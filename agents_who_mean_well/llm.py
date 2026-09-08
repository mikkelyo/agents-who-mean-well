"""Async client for a local vLLM OpenAI-compatible endpoint."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class Completion:
    """One sampled completion and the tokens it cost."""

    text: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        """Prompt plus completion, as reported by the server."""
        return self.prompt_tokens + self.completion_tokens


class LLM:
    """Semaphore-bounded vLLM client that accounts every token it spends."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        max_concurrency: int = 16,
        timeout: float = 120.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @property
    def total_tokens(self) -> int:
        """Every token this client has spent, across all calls."""
        return self.prompt_tokens + self.completion_tokens

    async def complete(
        self, *, prompt: str, max_tokens: int, temperature: float
    ) -> Completion:
        """Sample one completion, adding the server's usage to the running total."""
        async with self._semaphore:
            response = await self._client.post(
                "/v1/chat/completions",
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
        if response.status_code != httpx.codes.OK:
            # httpx omits the body, which is where vLLM explains the rejection.
            raise RuntimeError(f"vLLM {response.status_code}: {response.text}")

        payload = response.json()
        usage = payload["usage"]
        self.prompt_tokens += usage["prompt_tokens"]
        self.completion_tokens += usage["completion_tokens"]
        return Completion(
            text=payload["choices"][0]["message"]["content"],
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

    async def aclose(self) -> None:
        """Close the underlying connection pool."""
        await self._client.aclose()
