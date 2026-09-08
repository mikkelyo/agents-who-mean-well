"""Worker pool: sample, verify, update the budget, retry."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from agents_who_mean_well import budget, insight
from agents_who_mean_well.llm import LLM
from agents_who_mean_well.tasks import Task
from agents_who_mean_well.verifier import verify

logger = logging.getLogger(__name__)

INSTRUCTION = "Solve the problem. Reply with one Python code block and no prose."


@dataclass(frozen=True)
class RunConfig:
    """One experimental arm."""

    name: str
    model: str
    base_url: str = "http://localhost:8000"
    max_concurrency: int = 16
    token_budget_per_task: int = 20_000
    max_rounds: int = 8
    max_tokens: int = 1024
    temperature: float = 0.8
    verify_timeout: float = 10.0
    reallocate: bool = False
    share_insight: bool = False


@dataclass(frozen=True)
class TaskResult:
    """Outcome for one task: solved or not, and what it cost."""

    task_id: str
    solved: bool
    attempts: int
    tokens_spent: int


@dataclass
class _State:
    """Mutable per-task progress inside a run."""

    solved: bool = False
    attempts: int = 0
    tokens_spent: int = 0
    failures: list[insight.Failure] = field(default_factory=list)


def extract_code(text: str) -> str:
    """Pull the first fenced block out of a completion, or take it verbatim."""
    if "```" not in text:
        return text
    block = text.split("```", 2)[1]
    return block.split("\n", 1)[1] if block.startswith("python") else block


def _build_prompt(*, task: Task, state: _State, config: RunConfig) -> str:
    """Compose the attempt prompt, folding in insight when the arm shares it."""
    prompt = f"{INSTRUCTION}\n\n{task.prompt}"
    if not (config.share_insight and state.failures):
        return prompt
    note = insight.summarize(task_prompt=task.prompt, failures=state.failures)
    return f"{prompt}\n\nEarlier attempts failed:\n{note}"


async def _attempt(*, task: Task, state: _State, llm: LLM, config: RunConfig) -> None:
    """Sample one candidate, verify it, and fold the outcome into the state."""
    completion = await llm.complete(
        prompt=_build_prompt(task=task, state=state, config=config),
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )
    state.attempts += 1
    state.tokens_spent += completion.total_tokens

    code = extract_code(completion.text)
    result = await verify(code=code, tests=task.tests, timeout=config.verify_timeout)
    if result.passed:
        state.solved = True
    else:
        state.failures.append(insight.Failure(code=code, trace=result.trace))


async def run(*, tasks: list[Task], config: RunConfig, llm: LLM) -> list[TaskResult]:
    """Attempt every task in rounds until solved or out of allowance."""
    allowances = {task.task_id: config.token_budget_per_task for task in tasks}
    states = {task.task_id: _State() for task in tasks}
    total_budget = config.token_budget_per_task * len(tasks)

    for round_index in range(config.max_rounds):
        pending = [
            task
            for task in tasks
            if not states[task.task_id].solved
            and states[task.task_id].tokens_spent < allowances[task.task_id]
        ]
        if not pending:
            break

        logger.info("Round %d: %d tasks pending.", round_index, len(pending))
        await asyncio.gather(
            *(
                _attempt(task=task, state=states[task.task_id], llm=llm, config=config)
                for task in pending
            )
        )

        if config.reallocate:
            spent = sum(state.tokens_spent for state in states.values())
            allowances = budget.reallocate(
                progress=[
                    budget.TaskProgress(
                        task_id=task_id,
                        attempts=state.attempts,
                        solved=state.solved,
                        tokens_spent=state.tokens_spent,
                    )
                    for task_id, state in states.items()
                ],
                remaining_tokens=total_budget - spent,
            )

    return [
        TaskResult(
            task_id=task_id,
            solved=state.solved,
            attempts=state.attempts,
            tokens_spent=state.tokens_spent,
        )
        for task_id, state in states.items()
    ]
