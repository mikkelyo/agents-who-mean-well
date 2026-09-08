"""The verifier is the gate; a wrong verdict invalidates every number."""

from __future__ import annotations

from agents_who_mean_well.verifier import verify


async def test_correct_code_passes() -> None:
    result = await verify(
        code="def add(a, b): return a + b", tests="assert add(2, 3) == 5"
    )

    assert result.passed


async def test_wrong_code_fails_with_a_trace() -> None:
    result = await verify(
        code="def add(a, b): return a - b", tests="assert add(2, 3) == 5"
    )

    assert not result.passed
    assert "AssertionError" in result.trace


async def test_syntax_error_fails_without_hanging() -> None:
    result = await verify(code="def add(a, b) return", tests="assert True")

    assert not result.passed
    assert "SyntaxError" in result.trace


async def test_infinite_loop_times_out() -> None:
    result = await verify(code="while True: pass", tests="assert True", timeout=0.5)

    assert not result.passed
    assert "Timed out" in result.trace
