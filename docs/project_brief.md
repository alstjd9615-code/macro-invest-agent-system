# Project Brief — macro-invest-agent-platform

> **Status**: Draft — v0.1.0  
> **Owner**: Platform Engineering  
> **Last updated**: 2026-04-10

---

## 1. Problem Statement

Macroeconomic data — interest rates, inflation figures, employment statistics, yield curves — contains
rich investment signals, but translating those signals into structured, auditable decisions is hard.
Existing approaches suffer from one or more of:

- Opaque model outputs that cannot be traced back to inputs.
- Logic scattered across notebooks, scripts, and ad-hoc ML experiments.
- No clear boundary between deterministic rules and probabilistic model inference.
- No evaluation harness for AI-assisted analysis components.

## 2. Goal

Build a **production-oriented**, **learning-friendly** platform that:

1. Transforms macroeconomic time-series data into structured investment signals through a
   **deterministic, fully typed, testable** domain layer.
2. Exposes those signals to AI agents through a **read-only MCP tool layer** with typed schemas.
3. Enables AI agents to **summarise, review, and explain** signals without owning or overriding
   any investment logic.
4. Provides an **evaluation harness** for prompt regression, tool-call replay, and failure
   scenario testing.

This is both a functional system and a **learning environment** for AI-agent engineering,
MCP tool design, and evaluation harness construction.

## 3. What This Project Is Not

| Not in scope | Reason |
|---|---|
| Autonomous trading execution | Out of scope for MVP — decisions are advisory only |
| Real-time market data feeds | Batch macro data is sufficient for the learning goal |
| Production deployment manifests | Deferred to Phase 5 |
| Write-capable MCP tools | MVP constraint — agents are read-only consumers |
| Full backtesting engine | Deferred to Phase 2+ |

## 4. Success Criteria — MVP

- All signal computation is reproducible: given the same inputs, always get the same outputs.
- Every MCP tool call is validated, logged, and returns a typed response.
- Unit tests cover 100% of the deterministic domain functions.
- The evaluation harness can run prompt regression tests in CI.
- A new engineer can run `make install && make up && make test` from a clean checkout.

## 5. Architecture Summary

See [README.md](../README.md#2-architecture-overview) for the full layered diagram.

```
Agent Layer  →  MCP Tool Layer  →  Domain Layer  →  Storage
                                      ↑
                              Harness / Eval Layer
```

## 6. Technology Choices

| Concern | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | Strong typing, rich ecosystem, AI tooling maturity |
| Schema / validation | Pydantic v2 | Fast, typed, standard in AI/ML Python stacks |
| Configuration | pydantic-settings | Type-safe env var loading with secret masking |
| Structured logging | structlog | JSON-native, trace-ID-aware, easy to extend |
| API framework | FastAPI (Phase 2) | Async-first, OpenAPI generation, Pydantic integration |
| Linting / formatting | ruff | Fast, unified linter + formatter |
| Type checking | mypy (strict) | Catches interface errors before runtime |
| Testing | pytest | Industry standard, rich plugin ecosystem |
| Infrastructure | Docker Compose | Simple local parity with production services |
| Database | PostgreSQL 16 | Reliable, queryable, Alembic-compatible |
| Object store | MinIO | S3-compatible, local-first |

## 7. Phase Roadmap

> ⚠️ **Superseded — historical reference only.**
> This table was written before detailed chapter scoping began.  The labels and
> scope here **do not match** the active chapter roadmap in
> [`docs/roadmap.md`](./roadmap.md).  All sequencing and status decisions must
> be taken from `docs/roadmap.md`, which is the canonical source of truth.

| Phase (legacy) | Original focus | Active chapter equivalent |
|---|---|---|
| 1 — Foundation | Repository skeleton, core modules, local infra | Chapter 1 — Macro Data Foundation |
| 2 — Domain + MCP | Feature computation, signal engine, MCP tools | Chapter 2 — Macro Snapshot Layer |
| 3 — Agent Wiring | LLM agent integration, prompt templates | Chapter 3 — Macro Regime Engine |
| 4 — Data Pipelines | Real macro data ingestion, pipeline orchestration | Chapter 4 — Multi-Engine Analysis Hub |
| 5 — Harness + Eval | Prompt regression, tool replay, adversarial scenarios | Chapter 5 — Alerting |
| 6 — Observability | OpenTelemetry, metrics, alerting | Chapter 6 — AI Explanation Engine |
