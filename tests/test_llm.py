"""The token accounting is the measurement; these tests guard it."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from agents_who_mean_well.llm import LLM
from tests.conftest import fake_llm


async def test_usage_comes_from_the_server_not_an_estimate() -> None:
    llm = fake_llm(replies=["hello"], prompt_tokens=7)
    completion = await llm.complete(prompt="hi", max_tokens=16, temperature=0.0)

    assert completion.prompt_tokens == 7
    assert completion.completion_tokens == len("hello")
    assert completion.total_tokens == 7 + len("hello")


async def test_totals_accumulate_across_calls() -> None:
    llm = fake_llm(replies=["ab"], prompt_tokens=3)
    await llm.complete(prompt="hi", max_tokens=16, temperature=0.0)
    await llm.complete(prompt="hi", max_tokens=16, temperature=0.0)

    assert llm.prompt_tokens == 6
    assert llm.completion_tokens == 4
    assert llm.total_tokens == 10


async def test_concurrency_never_exceeds_the_semaphore() -> None:
    in_flight = 0
    peak = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "x"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )

    llm = LLM(
        base_url="http://fake",
        model="fake",
        max_concurrency=4,
        transport=httpx.MockTransport(handler),
    )
    await asyncio.gather(
        *(llm.complete(prompt="p", max_tokens=8, temperature=0.0) for _ in range(20))
    )

    assert peak <= 4


async def test_error_body_reaches_the_caller() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="context length exceeded")

    llm = LLM(
        base_url="http://fake", model="fake", transport=httpx.MockTransport(handler)
    )
    with pytest.raises(RuntimeError, match="context length exceeded"):
        await llm.complete(prompt="p", max_tokens=8, temperature=0.0)
