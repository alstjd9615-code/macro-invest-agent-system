# macro-invest-agent-platform

> A macroeconomic-data-driven investment decision engine with a deterministic core, an MCP tool layer, and an AI agent layer for research, review, and operational debugging.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Directory Structure](#3-directory-structure)
4. [Local Development Setup](#4-local-development-setup)
5. [Major Services](#5-major-services)
6. [Testing Strategy](#6-testing-strategy)
7. [MCP Tool Overview](#7-mcp-tool-overview)
8. [Roadmap](#8-roadmap)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Project Overview

`macro-invest-agent-platform` turns macroeconomic time-series data into structured investment signals through a pipeline that is fully deterministic, auditable, and observable.

Three distinct layers sit on top of that pipeline:

| Layer | Responsibility |
|-------|----------------|
| **Domain / Core** | Pure, deterministic feature computation and signal generation. No framework dependencies. |
| **MCP Tool Layer** | Read-only tools that expose domain outputs to AI agents via typed, validated interfaces. |
| **Agent Layer** | LLM-backed agents that summarise, review, and explain signals. Agents never override domain logic. |
| **Harness / Eval Layer** | Prompt regression testing, tool replay, and failure-scenario simulation for agent quality assurance. |

The platform is designed so that investment decisions are always traceable back to a deterministic function call with explicit inputs and outputs — not to an opaque model response.

---

## 2. Architecture Overview

### Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Deterministic core** | All feature computation and signal generation lives in `domain/`. Same inputs always produce the same outputs. |
| **Agent boundary enforcement** | Agents read signals through MCP tools. They cannot call domain functions directly or trigger writes. |
| **Read-only MCP (MVP)** | Every MCP tool is a query. No tool mutates state in the MVP. |
| **Typed schemas everywhere** | Pydantic v2 models define every domain boundary: raw data in, features out, signals out, tool I/O. |
| **Reproducibility first** | Every signal result includes the input snapshot and feature values used to produce it. |
| **Observability first** | Structured JSON logging with correlation IDs on every request. Explicit typed exception hierarchy. |
| **No direct DB access in MCP** | MCP tools receive pre-computed domain objects. Storage is accessed only through repository interfaces in `domain/`. |

### Layered Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Agent Layer                      │
│   (LLM agents: summarise, review, explain only)     │
└────────────────────┬────────────────────────────────┘
                     │  reads via
┌────────────────────▼────────────────────────────────┐
│                  MCP Tool Layer                     │
│   (typed, read-only tools — mcp/tools/)             │
└────────────────────┬────────────────────────────────┘
                     │  calls
┌────────────────────▼────────────────────────────────┐
│                  Domain Layer                       │
│   macro/features.py  ·  signals/engine.py           │
│   (pure functions, deterministic, fully typed)      │
└────────────────────┬────────────────────────────────┘
                     │  reads from
┌────────────────────▼────────────────────────────────┐
│               Storage / Pipelines                   │
│   PostgreSQL (signals, features)                    │
│   MinIO / S3 (raw data, artefacts)                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│              Harness / Eval Layer                   │
│   Prompt regression · Tool replay · Failure tests   │
│   (evals/ — runs independently, no production dep)  │
└─────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
macro-invest-agent-platform/
│
├── apps/                          # Runnable application entry points
│   ├── api/                       # FastAPI application (signal query API)
│   └── cli/                       # Click/Typer CLI for local runs and backfills
│
├── core/                          # Cross-cutting infrastructure (no domain logic)
│   ├── config/
│   │   └── settings.py            # Pydantic-Settings app configuration
│   ├── exceptions/
│   │   └── base.py                # Typed exception hierarchy
│   ├── logging/
│   │   └── logger.py              # Structured JSON logger factory
│   └── schemas/
│       └── common.py              # Shared base models, enums, and scalar types
│
├── domain/                        # All investment logic lives here
│   ├── macro/
│   │   ├── models.py              # MacroDataPoint, MacroDataset Pydantic models
│   │   └── features.py            # Pure deterministic feature functions
│   └── signals/
│       ├── models.py              # SignalResult, SignalDirection Pydantic models
│       └── engine.py              # Deterministic signal engine
│
├── mcp/                           # MCP tool layer (read-only)
│   ├── schemas/
│   │   ├── get_macro_features.py  # Input/output schemas for get_macro_features tool
│   │   └── run_signal_engine.py   # Input/output schemas for run_signal_engine tool
│   └── tools/
│       ├── get_macro_features.py  # Tool implementation: compute and return features
│       └── run_signal_engine.py   # Tool implementation: run engine, return signal
│
├── pipelines/                     # Data ingestion and transformation pipelines
│   └── macro_ingest/              # Macro data fetch → validate → store
│
├── storage/                       # Storage adapters and schema migrations
│   ├── repositories/              # Repository pattern interfaces
│   └── migrations/                # Alembic migration scripts
│
├── evals/                         # Harness / evaluation layer
│   ├── harness/                   # Prompt regression runner
│   ├── replays/                   # Recorded tool call replays
│   └── scenarios/                 # Failure and edge-case scenario definitions
│
├── tests/                         # Automated tests
│   ├── core/                      # Tests for core config, logging, exceptions
│   ├── domain/                    # Tests for macro features and signal engine
│   └── mcp/                       # Tests for MCP schema validation and tool logic
│
├── docs/
│   ├── adr/                       # Architecture Decision Records
│   │   └── 001-deterministic-core-and-agent-separation.md
│   ├── alerts/
│   │   └── prometheus_rules.yml   # Prometheus alert rule definitions
│   ├── dashboards/
│   │   └── macro_platform_overview.json  # Grafana dashboard (auto-provisioned)
│   ├── runbooks/                  # Operational runbooks for key alert scenarios
│   ├── deployment.md              # Deployment guide, health checks, rollback
│   ├── metrics.md                 # Prometheus metric catalogue
│   └── observability.md           # Tracing and structured logging guide
│
├── deploy/
│   ├── prometheus.yml             # Prometheus scrape config
│   └── grafana/provisioning/      # Grafana datasource + dashboard provisioning
│
├── .env.example                   # Environment variable template
├── docker-compose.yml             # Local development infrastructure
└── pyproject.toml                 # Project metadata, dependencies, tool config
```

---

## 4. Local Development Setup

### Prerequisites

| Tool | Minimum version | Notes |
|------|-----------------|-------|
| Python | 3.12 | Use `pyenv` or `mise` to manage versions |
| [uv](https://github.com/astral-sh/uv) | latest | Recommended package manager |
| Docker | 24+ | For local infrastructure |
| Docker Compose | v2 | Bundled with Docker Desktop |

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/macro-invest-agent-platform.git
cd macro-invest-agent-platform
```

### Step 2 — Install Python dependencies

```bash
# Recommended: using uv
uv sync --all-extras

# Alternative: using pip
pip install -e ".[dev]"
```

### Step 3 — Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in any required values. See [.env.example](.env.example) for documentation on each variable.

### Step 4 — Start local infrastructure

```bash
docker compose up -d
```

This brings up PostgreSQL and MinIO. Wait for the health checks to pass:

```bash
docker compose ps
```

### Step 5 — Run database migrations

```bash
alembic upgrade head
```

### Step 6 — Verify the setup

```bash
# Run the full test suite
pytest

# Type-check
mypy .

# Lint
ruff check .
ruff format --check .
```

All checks should pass on a clean install.

---

## 5. Major Services

### PostgreSQL

- **Purpose**: Persistent storage for computed features, signal results, and pipeline run metadata.
- **Local port**: `5432`
- **Connection**: configured via `DATABASE_URL` in `.env`
- **Migrations**: managed with [Alembic](https://alembic.sqlalchemy.org/)

### MinIO (S3-compatible object store)

- **Purpose**: Raw macro data files, pipeline artefacts, model artefacts, and eval snapshots.
- **Local API port**: `9000`
- **Local console port**: `9001` → open `http://localhost:9001` in a browser
- **Credentials**: set via `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` in `.env`

### FastAPI Application (`apps/api`)

- **Purpose**: HTTP API for querying signal results, feature values, and pipeline status.
- **Start locally**:

  ```bash
  uvicorn apps.api.main:app --reload
  ```

- **Docs**: `http://localhost:8000/docs`

---

## 6. Testing Strategy

Tests are located in `tests/` and mirror the source layout.

### Unit Tests — `tests/core/` and `tests/domain/`

Test individual functions and classes in complete isolation. No I/O, no external dependencies.

```
tests/core/   → config loading, logger output, exception hierarchy
tests/domain/ → macro feature functions (pure), signal engine (pure)
```

Key properties:

- Feature functions and the signal engine are pure — tests simply call the function with explicit inputs and assert on the output.
- Every edge case (missing data, zero values, boundary conditions) is tested explicitly.
- No mocking required for domain tests because there are no side effects.

### MCP Schema and Tool Tests — `tests/mcp/`

Test that MCP tool inputs are validated correctly and that tools return the expected typed output.

```
tests/mcp/ → schema validation (valid inputs, invalid inputs, missing fields)
             tool integration (tool receives domain output → returns correct schema)
```

Key properties:

- Tools are tested against fake/fixture domain data — no real DB or S3 calls.
- Both the happy path and malformed-input rejection are tested.

### Eval / Harness Tests — `evals/`

Not part of the standard `pytest` run. Executed separately in CI as a regression gate.

```
evals/harness/    → run a set of prompt + tool-call scenarios, compare output to golden fixtures
evals/replays/    → replay recorded MCP tool calls and assert responses are stable
evals/scenarios/  → adversarial and failure-mode tests (malformed data, out-of-range values)
```

Run evals:

```bash
pytest evals/ -m eval
```

### Running Tests

```bash
# All unit/integration tests
pytest

# With coverage report
pytest --cov=. --cov-report=term-missing

# MCP tests only
pytest tests/mcp/

# Domain tests only
pytest tests/domain/
```

---

## 7. MCP Tool Overview

MCP tools are **read-only** in the MVP. They accept typed input, call the domain layer, and return typed output. Agents never receive mutable handles to domain objects.

| Tool | Input schema | Output schema | Description |
|------|-------------|---------------|-------------|
| `get_macro_features` | `GetMacroFeaturesRequest` | `GetMacroFeaturesResponse` | Compute deterministic features from a macro dataset snapshot. |
| `run_signal_engine` | `RunSignalEngineRequest` | `RunSignalEngineResponse` | Run the signal engine against pre-computed features and return a structured signal result. |

### Tool design constraints

- Tools do **not** accept database connection objects or storage handles as arguments.
- Tools do **not** perform writes, even as side effects.
- All tool inputs and outputs are fully serialisable Pydantic models.
- Tools raise structured `MCPToolError` subtypes on failure — never raw exceptions.

### Example: `get_macro_features`

```python
from mcp.tools.get_macro_features import get_macro_features
from mcp.schemas.get_macro_features import GetMacroFeaturesRequest

request = GetMacroFeaturesRequest(
    dataset_id="us-macro-2024-q1",
    indicators=["cpi_yoy", "unemployment_rate", "fed_funds_rate"],
)
response = get_macro_features(request)
print(response.features)
```

### Example: `run_signal_engine`

```python
from mcp.tools.run_signal_engine import run_signal_engine
from mcp.schemas.run_signal_engine import RunSignalEngineRequest

request = RunSignalEngineRequest(
    features=response.features,
    strategy_id="base-macro-v1",
)
result = run_signal_engine(request)
print(result.signal_direction, result.confidence_score)
```

---

## 8. Roadmap

### Phase 1 — MVP (current)

- [x] Repository foundation: `core/`, `domain/`, `mcp/`, `tests/`, `docs/`
- [x] Deterministic feature computation (`domain/macro/features.py`)
- [x] Deterministic signal engine (`domain/signals/engine.py`)
- [x] Read-only MCP tools (`get_macro_features`, `run_signal_engine`)
- [x] Typed schemas for all domain boundaries
- [x] Structured logging and exception hierarchy
- [x] Unit and MCP tool tests
- [x] Local Docker infrastructure (Postgres, MinIO)
- [x] ADR-001: Deterministic Core and Agent Separation

### Phase 2 — Agent Integration

- [ ] LangChain / LangGraph agent wiring to MCP tools
- [ ] Agent prompt templates for signal review and explanation
- [ ] Agent output schema validation
- [ ] Conversation context persistence

### Phase 3 — Data Pipelines

- [ ] Real macro data ingestion (FRED, World Bank, BLS)
- [ ] Pipeline orchestration (Prefect or Dagster)
- [ ] Feature versioning and lineage tracking
- [ ] Alembic migrations for feature store tables

### Phase 4 — Harness and Eval

- [ ] Prompt regression harness (`evals/harness/`)
- [ ] Tool call replay framework (`evals/replays/`)
- [ ] Failure and adversarial scenario library (`evals/scenarios/`)
- [ ] CI integration for eval gate

### Phase 5 — Observability and Operations

- [x] **PR1 — End-to-end tracing**: OpenTelemetry spans across agent → MCP adapter → MCP tools → services → ingestion pipeline; OTel/structlog bridge for log–trace correlation; `core/tracing/` module; updated `docs/observability.md`
- [x] **PR2/3/4 — Metrics, Alerts, and Deployment**: Prometheus metrics (`core/metrics/`), Grafana dashboard, alert rules, operational runbooks, FastAPI app with `/health` `/readiness` `/metrics` endpoints, updated `docker-compose.yml` with Prometheus + Grafana.

---

## 9. Troubleshooting

### `docker compose up` fails with port conflict

**Symptom**: `bind: address already in use` on port `5432` or `9000`.

**Fix**: Stop the conflicting service or change the host port in `docker-compose.yml`:

```yaml
ports:
  - "15432:5432"   # use port 15432 instead
```

Update `DATABASE_URL` in `.env` to match the new port.

---

### `uv sync` fails with Python version error

**Symptom**: `requires-python = ">=3.12"` mismatch.

**Fix**: Ensure Python 3.12 is active:

```bash
python --version        # should print 3.12.x
pyenv install 3.12.9
pyenv local 3.12.9
uv sync --all-extras
```

---

### `pytest` reports import errors

**Symptom**: `ModuleNotFoundError: No module named 'core'`

**Fix**: Make sure the project is installed in editable mode:

```bash
pip install -e ".[dev]"
# or
uv sync --all-extras
```

---

### `alembic upgrade head` fails with `connection refused`

**Symptom**: Postgres container is not yet healthy.

**Fix**: Wait for the container to be ready, then retry:

```bash
docker compose up -d
docker compose ps          # confirm postgres is "healthy"
alembic upgrade head
```

---

### MinIO console is not accessible

**Symptom**: `http://localhost:9001` returns connection refused.

**Fix**: Confirm MinIO is running and the console port is mapped:

```bash
docker compose ps
docker compose logs minio
```

Check that `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` are set in `.env`.

---

### Type errors from `mypy`

**Symptom**: `error: Cannot find implementation or library stub for module named '...'`

**Fix**: Make sure all dependencies with type stubs are installed:

```bash
uv sync --all-extras
# or
pip install -e ".[dev]"
```

If a third-party library has no stubs, add it to `[[tool.mypy.overrides]]` in `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = "some_untyped_library.*"
ignore_missing_imports = true
```
