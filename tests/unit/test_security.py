"""Tests for the authentication dependency lists and the last-resort handler."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from template_project.presentation.api.security import AUTH_AND_CONTEXT, AUTH_ONLY
from template_project.presentation.api.v1.exception_handlers import (
    register_exception_handlers,
)

AUTH_HEADERS = {"Authorization": "Bearer test-service-api-key"}


@pytest.fixture
def client() -> TestClient:
    """Serve one route per dependency list, plus a route that always fails."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/body-less", dependencies=AUTH_ONLY)
    async def body_less() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/body-required", dependencies=AUTH_AND_CONTEXT)
    async def body_required() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/boom", dependencies=AUTH_ONLY)
    async def boom() -> dict[str, bool]:
        raise ValueError("nothing anticipated this")

    # Starlette re-raises an unhandled error after the last-resort handler responds.
    return TestClient(app, raise_server_exceptions=False)


class TestAuthOnly:
    """Cases for routes that authenticate without reading a body."""

    def test_serves_a_route_that_carries_no_body(self, client: TestClient) -> None:
        """Reading a body here would fail before the handler ever ran."""
        response = client.get("/body-less", headers=AUTH_HEADERS)

        assert response.status_code == 200

    def test_still_rejects_a_missing_token(self, client: TestClient) -> None:
        """Dropping the body dependency must not drop authentication with it."""
        response = client.get("/body-less")

        assert response.status_code == 401
        assert response.json()["ErrorCode"] == "api/authentication-error"


class TestAuthAndContext:
    """Cases for routes whose body carries the caller."""

    def test_reports_a_missing_body_as_a_bad_request(self, client: TestClient) -> None:
        """An unparseable body is the caller's fault, not a server failure."""
        response = client.get("/body-required", headers=AUTH_HEADERS)

        assert response.status_code == 400
        assert response.json()["ErrorCode"] == "api/validation-error"

    def test_reports_a_body_that_is_not_an_object(self, client: TestClient) -> None:
        """A JSON array parses but has no caller fields to read."""
        response = client.request(
            "GET", "/body-required", json=[1, 2], headers=AUTH_HEADERS
        )

        assert response.status_code == 400
        assert response.json()["ErrorCode"] == "api/validation-error"


class TestUnhandledExceptions:
    """Cases for failures no handler anticipated."""

    def test_renders_through_the_shared_error_contract(
        self, client: TestClient
    ) -> None:
        """Callers never see a bare 500 outside the documented error DTO."""
        response = client.get("/boom", headers=AUTH_HEADERS)

        assert response.status_code == 500
        assert response.json() == {
            "Type": "https://httpstatuses.com/500",
            "Title": "Internal Server Error",
            "Status": 500,
            "Detail": "An unexpected error occurred.",
            "ErrorCode": "api/error",
        }
