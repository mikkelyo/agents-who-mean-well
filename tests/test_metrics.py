"""Comparison arithmetic and run-file round-tripping."""

from __future__ import annotations

from pathlib import Path

from agents_who_mean_well.metrics import compare, load_summary, summarize, write_run
from agents_who_mean_well.orchestrator import TaskResult

RESULTS = [
    TaskResult(task_id="a", solved=True, attempts=1, tokens_spent=100),
    TaskResult(task_id="b", solved=False, attempts=4, tokens_spent=300),
]


def test_summarize_counts_solves_and_spend() -> None:
    summary = summarize(name="baseline", results=RESULTS)

    assert summary.solved == 1
    assert summary.tasks == 2
    assert summary.tokens == 400
    assert summary.solve_rate == 0.5
    assert summary.tokens_per_solve == 400


def test_an_arm_that_solved_nothing_costs_infinity() -> None:
    unsolved = [TaskResult(task_id="a", solved=False, attempts=8, tokens_spent=900)]

    assert summarize(name="x", results=unsolved).tokens_per_solve == float("inf")


def test_run_file_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "baseline.jsonl"
    write_run(path=path, name="baseline", results=RESULTS)

    assert load_summary(path) == summarize(name="baseline", results=RESULTS)


def test_compare_orders_by_solve_rate() -> None:
    table = compare(
        [
            summarize(name="worse", results=RESULTS[1:]),
            summarize(name="better", results=RESULTS[:1]),
        ]
    )
    lines = table.splitlines()

    assert lines[2].startswith("better")
    assert lines[3].startswith("worse")
