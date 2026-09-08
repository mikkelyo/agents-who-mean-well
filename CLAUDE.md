# CLAUDE.md

## Project
`agents_who_mean_well` — a harness for verifier-gated agent search against a local vLLM server.
Research code, not an app: the point is to measure whether adaptive budget
allocation + shared failure insight beats naive pass@k at matched token spend,
using the smallest model that can do the job on a single RTX 3080 (10GB).

## Stack
Python 3.12, asyncio, uv, ruff, pytest. No LangChain/LangGraph, no FastAPI, no DI
container. Talk to vLLM over its OpenAI-compatible endpoint with plain httpx.

## Layout
Flat package, no layers.

    agents_who_mean_well/llm.py           async vLLM client, semaphore, token accounting
    agents_who_mean_well/verifier.py      run candidate code in a subprocess sandbox
    agents_who_mean_well/tasks.py         load problems + hidden tests from JSONL
    agents_who_mean_well/budget.py        STUB — per-task token budget, reallocation policy
    agents_who_mean_well/insight.py       STUB — summarize failures, share across attempts
    agents_who_mean_well/orchestrator.py  sample -> verify -> update budget -> retry
    agents_who_mean_well/metrics.py       solve rate vs tokens spent, per strategy

`budget.py` and `insight.py` are the experiment; everything else is plumbing.
Their signatures are fixed by the orchestrator — do not change one without the
other. The naive pass@k baseline is the null policy (fixed budget, no
reallocation, no insight), not a separate module.

## Commands
```bash
uv run pytest
uv run ruff check .
uv run black .
uv run mypy .
```

## Conventions
- Line length 88. Docstrings are one line. Signatures are typed — never restate
  parameters or returns in prose.
- Keep it simple. Prefer clarity over cleverness, no premature abstraction.
- No defensive coding: no `if x is None` fallbacks, no redundant `except` paths
  that re-set a value the happy path already set. If something is required, make
  it required and let it fail clearly.
- Don't add comments unless the logic isn't self-evident; comment the *reason*,
  not the mechanism.
- Token accounting comes from the API `usage` field, prompt + completion, in
  every arm. This is the measurement — never estimate it.
- Solo repo: commit straight to main, small and often. Commits are the
  revert point; branches are only worth it for an experiment I might abandon.
