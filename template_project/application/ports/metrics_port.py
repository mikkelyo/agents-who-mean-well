"""Port for recording operational metrics."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricsPort(Protocol):
    """Hides the metrics backend from the use cases that record measurements."""

    def increment(self, *, name: str, value: int = 1) -> None:
        """Add ``value`` to the counter ``name``."""
        ...

    def record_duration(self, *, name: str, seconds: float) -> None:
        """Record how long an operation took."""
        ...
