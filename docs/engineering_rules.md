# Engineering Rules — macro-invest-agent-platform

> These rules define how code in this repository is written, structured, and reviewed.
> They exist to make the codebase safe, reviewable, and maintainable as the team grows.
> When in doubt, leave a clear `# TODO` rather than committing a shortcut.

---

## 1. Language and Type Safety

- **Python 3.12** is the minimum required runtime.
- All public functions, methods, and module-level variables **must** have type annotations.
- Run `mypy` in strict mode. Suppress errors only when unavoidable, and document why.
- Use `from __future__ import annotations` in modules with forward references.
- Prefer `str | None` over `Optional[str]` (Python 3.10+ union syntax).

## 2. Pydantic Everywhere on Boundaries

- Every domain boundary (API request/response, MCP tool I/O, signal result) **must** be a
  Pydantic v2 model.
- Use `ConfigDict(frozen=True)` on value-object models (read-only after construction).
- Add `description=` to every `Field(...)` for self-documenting OpenAPI output.
- Never use raw `dict` or `Any` to cross module boundaries — define a schema instead.

## 3. Deterministic Core

- All investment logic (feature computation, signal generation) lives in `domain/`.
- Domain functions **must** be pure: no side effects, no I/O, no randomness.
- Domain functions must be unit-testable with simple `assert` statements.
- Agents **cannot** call domain functions directly. All access goes through `mcp/tools/`.

## 4. Agent Boundary Rules

- Agents **read** signals through MCP tools. They **never write** in the MVP.
- Agents **never** implement, override, or invent investment logic.
- Agents **never** receive database connections, storage handles, or raw SQL.
- Any behaviour an agent needs must be implemented first in `domain/` and then exposed
  via a typed MCP tool schema.

## 5. MCP Tool Design

- Every MCP tool accepts a single typed Pydantic input model and returns a single typed
  Pydantic output model.
- Tools raise typed `MCPToolError` subtypes on failure — never raw exceptions.
- Tool implementations are thin: validate input → call domain → wrap result → return.
- Tools do not perform writes, even as side effects (Phase 1 + Phase 2 constraint).

## 6. Secrets and Sensitive Data

- Secrets (passwords, API keys, tokens) are stored in `pydantic.SecretStr` fields.
- Secrets are never logged, printed, or included in error `detail` payloads.
- The `.env` file is gitignored. Commit only `.env.example` with safe placeholder values.
- Never hardcode credentials in source code.

## 7. Logging

- All logging uses `core.logging.logger.get_logger(__name__)` — never `print()` or
  `logging.getLogger()` directly.
- Every log record that crosses a service boundary must include a `trace_id`.
- Log at `INFO` in production. Use `DEBUG` only for local development detail.
- Log events are named in `snake_case` verb-noun form: `signal_computed`, `tool_called`.
- Never log secrets, PII, or full request/response payloads at `INFO` or above.

## 8. Exceptions

- All custom exceptions inherit from `AppError` in `core/exceptions/base.py`.
- Every exception class has an explicit `error_code` (SCREAMING_SNAKE_CASE).
- Exception `detail` payloads are structured dicts — never raw strings.
- Catch exceptions at boundaries (API handlers, MCP tool wrappers). Let them propagate
  naturally within the domain.

## 9. Testing

- Unit tests live in `tests/` and mirror the source layout.
- Domain functions are tested without mocks (they are pure).
- External I/O (database, S3, HTTP) is mocked or faked in tests — never real.
- Test names use `test_<what>_<expected_behaviour>` naming.
- Every edge case and error path must have a dedicated test.
- Do not delete or skip existing tests to make a PR pass.

## 10. Code Organisation

- Modules are small and focused. One primary concept per file.
- `core/` contains infrastructure concerns only (config, logging, exceptions, schemas).
  No domain or business logic belongs there.
- `domain/` contains all investment logic. No framework imports.
- `mcp/` contains tool wrappers. No storage access or direct domain imports from agents.
- Circular imports are a design smell — resolve them by introducing an interface or schema.

## 11. Documentation

- Every public module has a module-level docstring explaining its purpose.
- Every public function and class has a docstring (Google or NumPy style, consistent
  within a module).
- Architecture decisions are recorded in `docs/adr/` using the ADR template.
- When adding a new subsystem, update `docs/project_brief.md` and `README.md`.

## 12. Pull Request Rules

- PRs are small and focused on a single concern.
- Every PR must pass `make lint`, `make typecheck`, and `make test` before review.
- Do not auto-merge. All PRs require at least one review.
- Use `# TODO(issue-number):` format for deferred work in code.
- Leave a comment in the PR description for any deliberate trade-off or deviation from
  these rules.
