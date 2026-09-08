"""Composition root for objects: the only module that may import every layer."""

# 2. Third-party
from anthropic import AsyncAnthropic
from dependency_injector import containers, providers

# 3. Application Core (5. Services live here too)
from config import settings
from template_project.application.completion_service import CompletionService
from template_project.application.ports.current_user_port import CurrentUserPort

# 4. Infrastructure
from template_project.infrastructure.anthropic.anthropic_completion_adapter import (
    AnthropicCompletionAdapter,
)
from template_project.infrastructure.clients.example_client import create_example_client
from template_project.infrastructure.logging.logger_factory import create_logger
from template_project.infrastructure.observability.logging_metrics_adapter import (
    LoggingMetricsAdapter,
)

# 6. Presentation
from template_project.presentation.user.context_var_current_user_adapter import (
    ContextVarCurrentUserAdapter,
)

PACKAGE_NAME = "template_project"


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------
class InfrastructureContainer(containers.DeclarativeContainer):
    """Clients, adapters and loggers that talk to the world outside the process."""

    # Overridden at the bottom of this module with a request-scoped adapter.
    current_user_service: providers.Dependency[CurrentUserPort] = providers.Dependency(
        instance_of=CurrentUserPort
    )

    # Handlers are installed once per process, so the logger is shared.
    logger = providers.Singleton(
        create_logger, name=PACKAGE_NAME, level=settings.log_level
    )

    # The SDK client owns a connection pool; creating one per request would leak them.
    anthropic_client = providers.Singleton(
        AsyncAnthropic,
        api_key=settings.anthropic_api_key,
        timeout=settings.anthropic_config.timeout_seconds,
        max_retries=settings.anthropic_config.max_retries,
    )

    # Stateless over the pooled client; reads the caller per call, not per instance.
    completion_adapter = providers.Singleton(
        AnthropicCompletionAdapter,
        client=anthropic_client,
        logger=logger,
        current_user=current_user_service,
        model=settings.anthropic_config.model,
        max_tokens=settings.anthropic_config.max_tokens,
        temperature=settings.anthropic_config.temperature,
    )

    # One recorder per operation, so measurements never bleed between requests.
    metrics_adapter = providers.Factory(
        LoggingMetricsAdapter,
        logger=logger,
        namespace=settings.metrics_config.namespace,
        enabled=settings.metrics_config.enabled,
    )

    # Wires the factory function, not the class, so construction stays in one place.
    example_client = providers.Singleton(
        create_example_client, config=settings.example_api_config
    )


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
class ServiceContainer(containers.DeclarativeContainer):
    """Use cases, wired to ports rather than to concrete adapters."""

    infrastructure: InfrastructureContainer = providers.DependenciesContainer()

    current_user_service: providers.Dependency[CurrentUserPort] = providers.Dependency(
        instance_of=CurrentUserPort
    )

    # A use case per request; it carries the caller's state for that request only.
    completion_service = providers.Factory(
        CompletionService,
        logger=infrastructure.logger,
        completion=infrastructure.completion_adapter,
        current_user=current_user_service,
        metrics=infrastructure.metrics_adapter,
        system_prompt=settings.completion_config.system_prompt,
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
class Container(containers.DeclarativeContainer):
    """Root container composing infrastructure and services."""

    current_user_service: providers.Dependency[CurrentUserPort] = providers.Dependency(
        instance_of=CurrentUserPort
    )

    infrastructure = providers.Container(
        InfrastructureContainer, current_user_service=current_user_service
    )

    services = providers.Container(
        ServiceContainer,
        infrastructure=infrastructure,
        current_user_service=current_user_service,
    )


container = Container()

# Request scope enters here: singletons above hold this adapter, which reads the
# ContextVar on every call, so infrastructure never learns about HTTP.
container.current_user_service.override(
    providers.Factory(
        ContextVarCurrentUserAdapter, logger=container.infrastructure.logger
    )
)
