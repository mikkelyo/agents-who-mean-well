"""Smoke test: the null policy runs end to end against a fake server."""

from __future__ import annotations

import pytest

from agents_who_mean_well.orchestrator import RunConfig, extract_code, run
from agents_who_mean_well.tasks import Task
from tests.conftest import SOLUTION, WRONG, fake_llm

TASK = Task(task_id="add", prompt="Write add(a, b).", tests="assert add(2, 3) == 5")
BASELINE = RunConfig(name="test", model="fake", max_rounds=3)


def test_extract_code_strips_the_python_fence() -> None:
    assert extract_code(SOLUTION) == "def add(a, b):\n    return a + b\n"


def test_extract_code_passes_bare_text_through() -> None:
    assert extract_code("def add(a, b): return a + b") == "def add(a, b): return a + b"


async def test_solves_a_task_and_stops_sampling() -> None:
    results = await run(tasks=[TASK], config=BASELINE, llm=fake_llm(replies=[SOLUTION]))

    assert results[0].solved
    assert results[0].attempts == 1
    assert results[0].tokens_spent > 0


async def test_retries_until_max_rounds_then_gives_up() -> None:
    results = await run(tasks=[TASK], config=BASELINE, llm=fake_llm(replies=[WRONG]))

    assert not results[0].solved
    assert results[0].attempts == BASELINE.max_rounds


async def test_stops_when_the_allowance_runs_out() -> None:
    config = RunConfig(
        name="test", model="fake", max_rounds=9, token_budget_per_task=60
    )
    results = await run(tasks=[TASK], config=config, llm=fake_llm(replies=[WRONG]))

    assert not results[0].solved
    assert results[0].attempts < config.max_rounds


async def test_null_policy_never_touches_the_stubs() -> None:
    results = await run(
        tasks=[TASK], config=BASELINE, llm=fake_llm(replies=[WRONG, SOLUTION])
    )

    assert results[0].solved
    assert results[0].attempts == 2


async def test_insight_arm_reaches_the_stub() -> None:
    config = RunConfig(name="test", model="fake", max_rounds=3, share_insight=True)
    with pytest.raises(NotImplementedError):
        await run(tasks=[TASK], config=config, llm=fake_llm(replies=[WRONG]))


async def test_reallocation_arm_reaches_the_stub() -> None:
    config = RunConfig(name="test", model="fake", max_rounds=3, reallocate=True)
    with pytest.raises(NotImplementedError):
        await run(tasks=[TASK], config=config, llm=fake_llm(replies=[WRONG]))
