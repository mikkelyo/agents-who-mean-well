"""Composition root for the HTTP process: builds and serves the FastAPI app."""

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from os import getenv

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from template_project.constants.context_keys import ContextKeys
from template_project.context import context
from template_project.di_container import container
from template_project.infrastructure.logging.logger_factory import configure_logging
from template_project.presentation.api import register_exception_handlers, router

configure_logging(level=settings.log_level)
logger = container.infrastructure.logger()

APP_NAME = getenv("APP_NAME", "template_project")
REQUEST_ID_HEADER = "X-Request-Id"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Open external clients on startup and close them on shutdown."""
    anthropic_client = container.infrastructure.anthropic_client()
    example_client = container.infrastructure.example_client()
    logger.info("Started %s version %s.", APP_NAME, settings.version)
    try:
        yield
    finally:
        await example_client.aclose()
        await anthropic_client.close()
        logger.info("Stopped %s.", APP_NAME)


app = FastAPI(
    title=APP_NAME,
    version=settings.version,
    root_path=getenv("SCRIPT_NAME", ""),
    docs_url="/apidocs",
    openapi_url="/apispec_1.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Tag each request with a correlation id and log how it was served."""
    request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    context.set(ContextKeys.REQUEST_ID, request_id)
    started = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "%s %s -> %s in %.3fs [%s]",
        request.method,
        request.url.path,
        response.status_code,
        time.perf_counter() - started,
        request_id,
    )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


register_exception_handlers(app)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=getenv("HOST", "127.0.0.1"),
        port=int(getenv("PORT", "8080")),
        reload=settings.is_local,
    )
