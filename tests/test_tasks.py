"""Dataset loading."""

from __future__ import annotations

from pathlib import Path

from agents_who_mean_well.tasks import load_tasks


def test_loads_one_task_per_line(dataset: Path) -> None:
    tasks = load_tasks(dataset)

    assert len(tasks) == 1
    assert tasks[0].task_id == "add"
    assert tasks[0].tests == "assert add(2, 3) == 5"


def test_blank_lines_are_skipped(dataset: Path) -> None:
    dataset.write_text(dataset.read_text() + "\n\n")

    assert len(load_tasks(dataset)) == 1
