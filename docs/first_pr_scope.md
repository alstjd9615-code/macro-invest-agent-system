# First PR Scope — macro-invest-agent-platform

> **Branch**: `copilot/build-initial-engineering-foundation`  
> **Goal**: Establish a safe, reviewable foundation that a new engineer can read in one sitting.

---

## What This PR Does

This PR focuses exclusively on repository foundation. It does **not** implement the signal engine,
data pipelines, or agent wiring.

### Files Added or Improved

| File | Purpose |
|---|---|
| `README.md` | Already existed; preserved and not modified in this PR |
| `pyproject.toml` | Project metadata, dependencies, ruff, mypy, pytest config |
| `.env.example` | Environment variable template with safe defaults |
| `docker-compose.yml` | Local PostgreSQL + MinIO, with API/dashboard placeholders commented out |
| `Makefile` | Developer commands: `install`, `format`, `lint`, `typecheck`, `test`, `test-unit`, `test-contract`, `up`, `down`, `logs` |
| `core/config/settings.py` | `pydantic-settings` typed app config with secret masking |
| `core/logging/logger.py` | structlog-based structured logger with `trace_id` context var support |
| `core/exceptions/base.py` | Typed exception hierarchy (`AppError` and domain-specific subclasses) |
| `core/schemas/common.py` | Shared Pydantic schemas: `FreshnessMetadata`, `AuditMetadata`, `ErrorDetail`, `BaseResponse` |
| `tests/core/test_settings.py` | Unit tests for settings defaults, env loading, secrets, validation |
| `tests/core/test_exceptions.py` | Unit tests for exception hierarchy, attributes, raise/catch |
| `tests/core/test_common_schemas.py` | Unit tests for all common schema models |
| `tests/core/test_logger.py` | Unit tests for trace ID and logger construction |
| `docs/project_brief.md` | Problem statement, goals, architecture summary, technology choices |
| `docs/engineering_rules.md` | Code quality, typing, logging, testing, and PR rules |
| `docs/first_pr_scope.md` | This document |
| `docs/adr/001-deterministic-core-and-agent-separation.md` | ADR for the most important architectural decision |
| Directory skeleton | `__init__.py` files for `core/`, `domain/`, `mcp/`, `apps/`, `tests/`, `evals/`, etc. |

---

## What This PR Deliberately Excludes

These items are deferred to future PRs with clear TODOs in code or docs:

- `domain/macro/` and `domain/signals/` implementations (Phase 2)
- `mcp/tools/` implementations (Phase 2)
- `apps/api/` FastAPI application (Phase 2)
- `storage/repositories/` and Alembic migrations (Phase 3)
- `pipelines/` data ingestion (Phase 3)
- `evals/` harness and scenarios (Phase 4)
- Real macro data source integrations (Phase 3+)
- Production deployment manifests (Phase 5)

---

## How to Review This PR

1. **Start with `docs/`** — read the project brief, engineering rules, and ADR-001 to
   understand the intent.
2. **Read `pyproject.toml`** — check dependency choices and tool configuration.
3. **Read `core/` modules** — each is small. Verify types, docstrings, and secret handling.
4. **Read `tests/core/`** — confirm each test covers a meaningful case and is readable.
5. **Check `docker-compose.yml` and `Makefile`** — confirm local dev workflow is coherent.
6. **Check `.env.example`** — confirm no secrets, sensible defaults documented.

---

## Local Verification

```bash
# Install dependencies
make install

# Run all checks
make lint
make typecheck
make test

# Start infrastructure
make up
```

All four commands should succeed on a clean Python 3.12 environment.

---

## Open Questions / Deferred TODOs

- Should `core/schemas/common.py` include a standard pagination schema? → defer to Phase 2 when the API layer is implemented.
- Should `AuditMetadata` include a `user_id` field? → defer until authentication layer is designed.
- Should `docker-compose.yml` include a PgAdmin or MinIO bucket initialisation container? → nice to have, revisit in Phase 2.
