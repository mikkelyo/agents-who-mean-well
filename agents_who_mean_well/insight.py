"""Summarize verifier failures into guidance shared across sibling attempts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Failure:
    """One rejected candidate and the verifier trace that rejected it."""

    code: str
    trace: str


def summarize(*, task_prompt: str, failures: list[Failure]) -> str:
    """Condense failures into a note appended to the next attempt's prompt.

    Called before each retry when the arm enables insight, with every failure the
    task has accumulated. Returning a longer note costs prompt tokens on every
    subsequent attempt, and that spend counts against the same budget as sampling.
    """
    raise NotImplementedError
