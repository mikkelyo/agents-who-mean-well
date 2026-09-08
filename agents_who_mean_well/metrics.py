"""Solve rate against token spend, compared across arms."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from agents_who_mean_well.orchestrator import TaskResult


@dataclass(frozen=True)
class ArmSummary:
    """What one arm achieved and what it cost."""

    name: str
    tasks: int
    solved: int
    tokens: int

    @property
    def solve_rate(self) -> float:
        """Fraction of tasks the arm solved."""
        return self.solved / self.tasks

    @property
    def tokens_per_solve(self) -> float:
        """Spend per solved task; infinite for an arm that solved nothing."""
        return self.tokens / self.solved if self.solved else float("inf")


def summarize(*, name: str, results: list[TaskResult]) -> ArmSummary:
    """Reduce one arm's per-task results to its headline numbers."""
    return ArmSummary(
        name=name,
        tasks=len(results),
        solved=sum(result.solved for result in results),
        tokens=sum(result.tokens_spent for result in results),
    )


def write_run(*, path: Path, name: str, results: list[TaskResult]) -> None:
    """Persist one arm's per-task results as JSONL."""
    rows = [json.dumps({"arm": name, **asdict(result)}) for result in results]
    path.write_text("\n".join(rows) + "\n")


def load_summary(path: Path) -> ArmSummary:
    """Rebuild an arm summary from a run file written by ``write_run``."""
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return ArmSummary(
        name=rows[0]["arm"],
        tasks=len(rows),
        solved=sum(row["solved"] for row in rows),
        tokens=sum(row["tokens_spent"] for row in rows),
    )


def compare(summaries: list[ArmSummary]) -> str:
    """Render arms as a table, best solve rate first."""
    header = f"{'arm':<20}{'solved':>10}{'rate':>10}{'tokens':>12}{'tok/solve':>12}"
    lines = [header, "-" * len(header)]
    for summary in sorted(summaries, key=lambda s: s.solve_rate, reverse=True):
        lines.append(
            f"{summary.name:<20}"
            f"{f'{summary.solved}/{summary.tasks}':>10}"
            f"{summary.solve_rate:>10.1%}"
            f"{summary.tokens:>12,}"
            f"{summary.tokens_per_solve:>12,.0f}"
        )
    return "\n".join(lines)
