"""Tests for the HTTP contract of the completion endpoint."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from app import app
from template_project.di_container import container

AUTH_HEADERS = {"Authorization": "Bearer test-service-api-key"}
VALID_BODY = {"Prompt": "What is six times seven?", "UserId": "u-1", "UserName": "Ada"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Serve the app with the language model replaced by a stub."""
    adapter = MagicMock()
    adapter.complete = AsyncMock(return_value="42")
    container.infrastructure.completion_adapter.override(providers.Object(adapter))
    try:
        yield TestClient(app)
    finally:
        container.infrastructure.completion_adapter.reset_override()


class TestHealth:
    """Cases for the liveness probe."""

    def test_reports_ok(self, client: TestClient) -> None:
        """The probe is unauthenticated and returns plain text."""
        response = client.get("/test")

        assert response.status_code == 200
        assert response.text == "OK"

    def test_reports_an_unknown_route_as_a_plain_error(
        self, client: TestClient
    ) -> None:
        """A 404 keeps its status instead of being rendered as an auth failure."""
        response = client.get("/does-not-exist")

        assert response.status_code == 404
        assert response.json() == {
            "Type": "https://httpstatuses.com/404",
            "Title": "Not Found",
            "Status": 404,
            "Detail": "Not Found",
            "ErrorCode": "api/error",
        }


class TestCreateCompletion:
    """Cases for ``POST /v1/completions``."""

    def test_answers_in_pascal_case(self, client: TestClient) -> None:
        """The wire contract is PascalCase while Python stays snake_case."""
        response = client.post("/v1/completions", json=VALID_BODY, headers=AUTH_HEADERS)

        assert response.status_code == 200
        assert response.json() == {"Answer": "42", "RequestedBy": "u-1"}

    def test_rejects_a_missing_token(self, client: TestClient) -> None:
        """Routes carry the composed authentication dependencies."""
        response = client.post("/v1/completions", json=VALID_BODY)

        assert response.status_code == 401
        assert response.json()["ErrorCode"] == "api/authentication-error"

    def test_rejects_an_invalid_payload(self, client: TestClient) -> None:
        """Payload failures are rendered through the shared error DTO."""
        body = {"UserId": "u-1", "UserName": "Ada"}

        response = client.post("/v1/completions", json=body, headers=AUTH_HEADERS)

        assert response.status_code == 400
        assert response.json()["Errors"]

    def test_rejects_a_body_without_a_caller(self, client: TestClient) -> None:
        """An unidentified caller never reaches the use case."""
        body = {"Prompt": "Hello", "UserId": "", "UserName": ""}

        response = client.post("/v1/completions", json=body, headers=AUTH_HEADERS)

        assert response.status_code == 401

    def test_rejects_a_body_that_is_not_json(self, client: TestClient) -> None:
        """The caller dependency reads the body before FastAPI validates it."""
        response = client.post(
            "/v1/completions",
            content="not json",
            headers={**AUTH_HEADERS, "Content-Type": "application/json"},
        )

        assert response.status_code == 400
        assert response.json()["ErrorCode"] == "api/validation-error"
