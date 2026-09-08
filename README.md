# agents_who_mean_well

Does adaptive budget allocation plus shared failure insight beat naive pass@k at a
matched token budget? This is the rig that answers it, against a local vLLM server
running the smallest model that can do the job on one RTX 3080.

## Run it

Serve the model (on the 3080 box):

```bash
vllm serve Qwen/Qwen2.5-Coder-7B-Instruct-AWQ \
  --max-model-len 4096 --gpu-memory-utilization 0.90
```

Then run both arms and compare:

```bash
uv sync
uv run python scripts/run.py configs/baseline.yaml   # null policy = naive pass@k
uv run python scripts/run.py configs/adaptive.yaml   # needs the stubs implemented
uv run python scripts/eval.py
```

`--tasks` points at the dataset (default `data/tasks.jsonl`), one JSON object per
line with `task_id`, `prompt` and `tests`. Results land in `runs/<arm>.jsonl`.

## What's where

    agents_who_mean_well/llm.py           async vLLM client, semaphore, token accounting
    agents_who_mean_well/verifier.py      run candidate code in a subprocess sandbox
    agents_who_mean_well/tasks.py         load problems + hidden tests from JSONL
    agents_who_mean_well/budget.py        STUB — per-task budget, reallocation policy
    agents_who_mean_well/insight.py       STUB — summarize failures, share across attempts
    agents_who_mean_well/orchestrator.py  sample -> verify -> update budget -> retry
    agents_who_mean_well/metrics.py       solve rate vs tokens spent, per strategy

`budget.py` and `insight.py` are the experiment; everything else is plumbing. Both
raise `NotImplementedError`, so `configs/adaptive.yaml` fails until they are written.
`configs/baseline.yaml` runs today: it takes neither branch, which is what makes it
the null policy rather than a second code path that can drift.

## Measurement rules

Token counts come from the API `usage` field, prompt plus completion, in every arm —
never estimated. `scripts/run.py` logs the client's own running total next to the sum
of per-task spend; if they disagree, the accounting is broken and the numbers are void.

The verifier runs each candidate in a temporary directory under a timeout, inside a
network-less namespace via `unshare` where the kernel offers one. On macOS it falls
back to a plain subprocess, so trust the isolation on the Linux box, not the laptop.

```bash
uv run pytest
uv run ruff check .
uv run black .
uv run mypy .
```
