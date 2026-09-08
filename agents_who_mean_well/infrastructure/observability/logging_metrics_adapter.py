"""Metrics recorder that writes to the application log."""

from logging import Logger


class LoggingMetricsAdapter:
    """Implements :class:`MetricsPort`, so no metrics vendor leaks into use cases."""

    def __init__(self, *, logger: Logger, namespace: str, enabled: bool) -> None:
        self._logger = logger
        self._namespace = namespace
        self._enabled = enabled

    def increment(self, *, name: str, value: int = 1) -> None:
        """Add ``value`` to the counter ``name``."""
        self._emit(name=name, measurement=f"count={value}")

    def record_duration(self, *, name: str, seconds: float) -> None:
        """Record how long an operation took."""
        self._emit(name=name, measurement=f"seconds={seconds:.4f}")

    def _emit(self, *, name: str, measurement: str) -> None:
        if self._enabled:
            self._logger.info("metric %s.%s %s", self._namespace, name, measurement)
