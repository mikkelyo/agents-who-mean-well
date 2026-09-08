"""Load code-generation problems and their hidden tests from JSONL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Task:
    """One problem: the prompt to solve and the tests that decide it."""

    task_id: str
    prompt: str
    tests: str


def load_tasks(path: Path) -> list[Task]:
    """Read one task per non-empty line of a JSONL dataset."""
    lines = path.read_text().splitlines()
    return [Task(**json.loads(line)) for line in lines if line.strip()]
