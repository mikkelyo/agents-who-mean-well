"""Version 1 of the HTTP API."""

from fastapi import APIRouter

from agents_who_mean_well.presentation.api.v1 import completion_endpoints, health
from agents_who_mean_well.presentation.api.v1.exception_handlers import (
    register_exception_handlers,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(completion_endpoints.router, prefix="/v1")

__all__ = ["register_exception_handlers", "router"]
