# template-project

A Python service template built as **ports and adapters** (clean architecture):
FastAPI at the edge, use cases in the middle, vendor SDKs at the rim, and a single
dependency-injection container wiring them together.

## Quick start

```bash
uv sync --extra dev

export ANTHROPIC_API_KEY=sk-ant-...      # required
export SERVICE_API_KEY=local-dev-token   # required, callers present it as a bearer token
export APP_ENV_NAME=local                # optional, defaults to "local"

uv run python app.py                     # serves http://127.0.0.1:8080
curl http://127.0.0.1:8080/test          # -> OK
curl -X POST http://127.0.0.1:8080/v1/completions \
  -H "Authorization: Bearer local-dev-token" -H "Content-Type: application/json" \
  -d '{"Prompt":"What is six times seven?","UserId":"u-1","UserName":"Ada"}'
```

Secrets may also live in `.secrets.json` or `.env` (both gitignored); non-secret
values belong in the committed `settings.json`. Interactive docs are at `/apidocs`.

## Starting a new project from this template

```bash
uv run python scripts/rename_project.py my_app   # moves the package, rewrites the name, relocks
uv run pytest
```

It needs a clean tree, and prints the steps it deliberately leaves to you. Review it
with `git diff HEAD`; `git reset --hard` undoes the whole thing.

Then delete the `example_client` / `example_api_config` scaffolding: it exists only to
demonstrate the `RestClient` + factory-function pattern, and it is referenced from
`app.py`, `config.py`, `di_container.py` and two test modules.

```bash
uv run pytest          # tests
uv run ruff check .    # lint
uv run black .         # format
uv run mypy .          # type check
```

## Layer map

```
app.py                        composition root: middleware, routers, lifespan
config.py                     composition root: Dynaconf -> Pydantic `settings`
settings.json                 non-secret configuration (committed)
conftest.py                   sets required env vars before `config` is imported
scripts/rename_project.py     one-shot rename when cloning this template
template_project/
├── di_container.py           composition root: all wiring
├── context.py                ContextVar registry for request-scoped state
├── constants/                frozen strings: context keys, user-facing messages
├── domain/                   pure: no framework, no I/O
│   ├── enums/                APIErrorCode, Environment, MessageRole
│   ├── exceptions/           APIException + Authentication/Validation subclasses
│   ├── user/                 CurrentUser
│   └── conversation/         Message, CompletionResult
├── application/              use cases + ports
│   ├── ports/                typing.Protocol interfaces, one file per port
│   ├── configurations/       config a use case owns, independent of any vendor
│   └── completion_service.py use case
├── infrastructure/           adapters; every vendor SDK import lives here
│   ├── configurations/       one Pydantic config model per external system
│   ├── clients/              async httpx clients (base/ + concrete + factory fn)
│   ├── anthropic/            completion adapter
│   ├── logging/              logger factory
│   └── observability/        metrics adapter
└── presentation/             HTTP edge
    ├── api/                  security.py + v1/ routers and exception handlers
    ├── request_models/       inbound DTOs (PascalCase on the wire)
    ├── response_models/      outbound DTOs
    └── user/                 ContextVar adapter satisfying CurrentUserPort
```

## The dependency rule

`presentation → application → domain` and `infrastructure → application.ports + domain`.

- `domain` imports nothing from other layers — stdlib and Pydantic only.
- `application` imports `domain` and its own `ports`. Never `infrastructure`,
  never `presentation`, never a vendor SDK. Needs an external capability? Add a port.
- `infrastructure` holds every vendor SDK and all I/O, and converts vendor types to
  domain types at the boundary — including vendor exceptions.
- `presentation` holds FastAPI, DTOs and auth, and reaches use cases through the container.
- `di_container.py` is the only module allowed to import from every layer.

Ports are `@runtime_checkable` `Protocol`s with keyword-only methods. Adapters **do not
subclass** them; conformance is structural and asserted in tests with
`assert isinstance(adapter, SomePort)`.

## How a request flows

```
POST /v1/completions
  -> AUTH_AND_CONTEXT     bearer token checked, CurrentUser bound to the ContextVar
  -> CompletionRequestModel
  -> container.services.completion_service()
  -> CompletionService.complete()          reads CurrentUserPort, records MetricsPort
  -> CompletionPort
  -> AnthropicCompletionAdapter            the only code that knows the SDK exists
  -> CompletionResponseModel               serialised PascalCase
```

`ContextVarCurrentUserAdapter` is how request scope reaches singleton infrastructure:
the container overrides the root `current_user_service` dependency with it, and the
singletons that hold it read the ContextVar on every call.

Every failure leaves through `exception_handlers.py`, including ones nothing
anticipated: an `Exception` handler renders them as the same error DTO and logs the
traceback, so no caller ever sees a bare 500.

## Adding a port, adapter and use case

1. **Port** — `application/ports/<name>_port.py`: `from __future__ import annotations`,
   a `@runtime_checkable class <Name>Port(Protocol)` whose docstring says what the port
   *hides*, and keyword-only methods with `...` bodies.
2. **Config** — a Pydantic model, every field with a default, validation bounds and a
   `description=`. Put it in `infrastructure/configurations/<system>_config.py` when it
   configures an external system, or `application/configurations/<use case>_config.py`
   when the use case owns it and swapping vendors would not change it. Add it to
   `Settings` in `config.py` and give it a block in `settings.json`. Use
   `EnvNameString` for names that must be scoped per environment.
3. **Adapter** — `infrastructure/<vendor>/<name>_adapter.py`: a plain class with a
   keyword-only constructor whose docstring names the port it implements. Do not
   subclass the port. Translate vendor types *and* vendor exceptions at the boundary.
4. **Use case** — `application/<thing>_service.py`: keyword-only constructor, every
   collaborator injected and typed by its port, raising domain exceptions only.
5. **Wiring** — in `di_container.py`, add the adapter to `InfrastructureContainer`
   (`Singleton` for process-wide state, `Factory` for per-request objects) and the use
   case to `ServiceContainer`. Pass `some_provider.provider` when a use case needs a
   *factory* rather than an instance, and `Factory(partial, fn, dep)` to hand the
   application layer a zero-argument callable.
6. **Endpoint** — add `presentation/api/v1/<feature>_endpoints.py`, resolve the use case
   inside the handler body with `container.services.<x>()`, apply
   `responses=ERROR_RESPONSES`, and include the router from
   `presentation/api/v1/__init__.py`. Pick the dependency list by whether the route has
   a body: `AUTH_AND_CONTEXT` reads the caller from it, so a GET or any body-less route
   takes `AUTH_ONLY` instead and reaches the caller some other way.
7. **Tests** — one module per adapter and use case in `tests/unit/`, every collaborator a
   `MagicMock()`, and a case in `tests/unit/test_di_container.py` that resolves the new
   provider and asserts it satisfies its port. That file is the only guard against
   silent wiring drift.

## Conventions

- A one-line docstring on every module, class and public function. Signatures are
  typed, so do not restate parameters and return values in prose; use a `#` comment
  where the *reason* for the code is not obvious.
- Keyword-only constructors and keyword-only public method parameters.
- DTOs use `ConfigDict(validate_by_name=True)` with PascalCase `alias=`, so the wire
  contract is PascalCase while Python stays snake_case.
- User-facing strings live in `constants/static_messages.py`; context keys in
  `constants/context_keys.py`.
- File names state the role: `*_port.py`, `*_service.py`, `*_adapter.py`, `*_client.py`,
  `*_config.py`, `*_endpoints.py`, `*_request_model.py`, `*_response_model.py`.
