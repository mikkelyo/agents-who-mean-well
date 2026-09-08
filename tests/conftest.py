"""Shared fixtures: a fake vLLM server and a two-task dataset."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from agents_who_mean_well.llm import LLM

SOLUTION = "```python\ndef add(a, b):\n    return a + b\n```"
WRONG = "```python\ndef add(a, b):\n    return a - b\n```"


def fake_llm(*, replies: list[str], prompt_tokens: int = 10) -> LLM:
    """An LLM whose server returns ``replies`` in order, then repeats the last."""
    remaining = list(replies)

    def handler(request: httpx.Request) -> httpx.Response:
        text = remaining.pop(0) if len(remaining) > 1 else remaining[0]
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": text}}],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": len(text),
                },
            },
        )

    return LLM(
        base_url="http://fake",
        model="fake-model",
        transport=httpx.MockTransport(handler),
    )


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    """A JSONL file holding one solvable task."""
    path = tmp_path / "tasks.jsonl"
    path.write_text(
        json.dumps(
            {
                "task_id": "add",
                "prompt": "Write add(a, b).",
                "tests": "assert add(2, 3) == 5",
            }
        )
        + "\n"
    )
    return path
