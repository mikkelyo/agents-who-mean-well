"""Run one experimental arm and write its per-task results to runs/."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import yaml

from agents_who_mean_well.llm import LLM
from agents_who_mean_well.metrics import summarize, write_run
from agents_who_mean_well.orchestrator import RunConfig, run
from agents_who_mean_well.tasks import load_tasks

logger = logging.getLogger("run")


async def main() -> None:
    """Load an arm's config, run it against the dataset, and record the result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config", type=Path, help="Arm config, e.g. configs/baseline.yaml"
    )
    parser.add_argument("--tasks", type=Path, default=Path("data/tasks.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    )
    config = RunConfig(**yaml.safe_load(args.config.read_text()))
    tasks = load_tasks(args.tasks)
    llm = LLM(
        base_url=config.base_url,
        model=config.model,
        max_concurrency=config.max_concurrency,
    )
    try:
        results = await run(tasks=tasks, config=config, llm=llm)
    finally:
        await llm.aclose()

    args.out.mkdir(exist_ok=True)
    write_run(path=args.out / f"{config.name}.jsonl", name=config.name, results=results)

    summary = summarize(name=config.name, results=results)
    logger.info(
        "%s solved %d/%d for %d tokens (client total %d).",
        summary.name,
        summary.solved,
        summary.tasks,
        summary.tokens,
        llm.total_tokens,
    )


if __name__ == "__main__":
    asyncio.run(main())
