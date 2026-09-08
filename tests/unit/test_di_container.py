"""Resolves every provider in the real container to catch silent wiring drift."""

from anthropic import AsyncAnthropic

from template_project.application.completion_service import CompletionService
from template_project.application.ports.completion_port import CompletionPort
from template_project.application.ports.current_user_port import CurrentUserPort
from template_project.application.ports.metrics_port import MetricsPort
from template_project.di_container import container
from template_project.infrastructure.anthropic.anthropic_completion_adapter import (
    AnthropicCompletionAdapter,
)
from template_project.infrastructure.clients.example_client import ExampleClient
from template_project.infrastructure.observability.logging_metrics_adapter import (
    LoggingMetricsAdapter,
)
from template_project.presentation.user.context_var_current_user_adapter import (
    ContextVarCurrentUserAdapter,
)


class TestInfrastructureContainer:
    """Every infrastructure provider resolves and satisfies its port."""

    def test_logger_is_shared_across_the_process(self) -> None:
        """A second logger would install a second set of handlers."""
        assert container.infrastructure.logger() is container.infrastructure.logger()

    def test_anthropic_client_is_shared_across_the_process(self) -> None:
        """The SDK client owns a connection pool, so it must be a singleton."""
        assert (
            container.infrastructure.anthropic_client()
            is container.infrastructure.anthropic_client()
        )
        assert isinstance(container.infrastructure.anthropic_client(), AsyncAnthropic)

    def test_completion_adapter_satisfies_the_completion_port(self) -> None:
        """Adapters conform structurally, so conformance is asserted here."""
        adapter = container.infrastructure.completion_adapter()

        assert isinstance(adapter, AnthropicCompletionAdapter)
        assert isinstance(adapter, CompletionPort)

    def test_metrics_adapter_is_created_per_use(self) -> None:
        """A recorder is per-operation, so the provider must be a factory."""
        first = container.infrastructure.metrics_adapter()
        second = container.infrastructure.metrics_adapter()

        assert isinstance(first, LoggingMetricsAdapter)
        assert isinstance(first, MetricsPort)
        assert first is not second

    def test_example_client_is_shared_across_the_process(self) -> None:
        """The client keeps a pooled httpx client, so it must be a singleton."""
        client = container.infrastructure.example_client()

        assert isinstance(client, ExampleClient)
        assert client is container.infrastructure.example_client()


class TestServiceContainer:
    """Every use case resolves with its collaborators wired to ports."""

    def test_completion_service_is_created_per_request(self) -> None:
        """A use case carries per-request state, so it must be a factory."""
        first = container.services.completion_service()
        second = container.services.completion_service()

        assert isinstance(first, CompletionService)
        assert first is not second


class TestCurrentUserOverride:
    """The request-scoped dependency is bound to the presentation adapter."""

    def test_resolves_to_the_context_var_adapter(self) -> None:
        """This override is how request scope reaches singleton infrastructure."""
        current_user = container.current_user_service()

        assert isinstance(current_user, ContextVarCurrentUserAdapter)
        assert isinstance(current_user, CurrentUserPort)
