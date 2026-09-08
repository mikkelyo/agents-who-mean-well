"""HTTP API surface."""

from template_project.presentation.api.v1 import register_exception_handlers, router

__all__ = ["register_exception_handlers", "router"]
