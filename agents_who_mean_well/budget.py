"""Per-task token budget and the policy that reallocates it between rounds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskProgress:
    """What one task has consumed and achieved so far this run."""

    task_id: str
    attempts: int
    solved: bool
    tokens_spent: int


def reallocate(
    *, progress: list[TaskProgress], remaining_tokens: int
) -> dict[str, int]:
    """Divide the run's remaining tokens across tasks, keyed by task id.

    Called after every round when the arm enables reallocation; the null policy
    never calls it and keeps each task on its opening allowance. The return value
    replaces all allowances, so solved tasks belong in it at their current spend
    or not at all. Spending the whole remainder is not required, but anything
    withheld is never offered again.
    """
    raise NotImplementedError
