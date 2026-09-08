"""Request-scoped value registry backed by :mod:`contextvars`."""

from contextvars import ContextVar
from typing import Any


class Context:
    """Lazy registry of context variables keyed by :class:`ContextKeys`."""

    def __init__(self) -> None:
        self.registry: dict[str, ContextVar] = {}

    def _get_context_var(self, key: str, default: Any = None) -> ContextVar:
        """Return the context variable for ``key``, creating it on first use."""
        if key not in self.registry:
            self.registry[key] = ContextVar(key, default=default)
        return self.registry[key]

    def set(self, key: str, value: Any) -> None:
        """Bind ``value`` to ``key`` for the current context."""
        self._get_context_var(key).set(value)

    def get(self, key: str, default: Any = None) -> Any:
        """Read the value bound to ``key`` in the current context."""
        return self._get_context_var(key, default).get()


context = Context()
