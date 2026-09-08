"""Liveness endpoint."""

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from template_project.constants.static_messages import StaticMessages

router = APIRouter(tags=["health"])


@router.get("/test", response_class=PlainTextResponse)
async def test() -> PlainTextResponse:
    """Report that the process is serving traffic."""
    return PlainTextResponse(StaticMessages.HEALTH_OK, status_code=status.HTTP_200_OK)
