# macro-invest-agent-platform

**A multi-engine macro investment intelligence platform that converts raw economic data into deterministic, analyst-interpretable regime signals with explicit trust semantics.**

---

## Why this project exists

Most macro investment tooling gives analysts either raw data or opaque model outputs. Neither is useful at decision time. This platform builds the middle layer: a deterministic, auditable pipeline that classifies the macroeconomic regime, scores conviction across five analytical dimensions, flags data quality problems separately from analytical disagreements, and surfaces structured explanations that an analyst can read, challenge, and act on.

The core design contract is that every output is **reproducible, explainable, and honest about its own limitations**.

---

## What the platform does

Given a set of macro indicator observations (GDP growth, inflation, labour market, policy, financial conditions), the platform:

1. Normalises and quality-checks the raw data (freshness, completeness, source attribution)
2. Builds a structured macro **snapshot** — a point-in-time state vector per category
3. Computes **quant dimension scores** (five dimensions, [0.0–1.0], with breadth/momentum/change-intensity secondaries)
4. Classifies a **macro regime** (9 labels: goldilocks → contraction; 6 families)
5. Derives **regime and signal confidence** informed by quant scores, data freshness, and degraded state
6. Detects **analytical conflict** — when macro drivers are internally contested, independent of data quality
7. Generates **investment signals** grounded in the regime, with supporting/conflicting drivers per signal
8. Builds **structured narrative explanations** surfaced via a read-only analyst API and a Streamlit workbench

---

## Core system flow

```
Macro Observations (GDP, CPI, unemployment, rates, spreads...)
    │
    ▼
Normalization / Freshness / Quality Check
    │  freshness_status: fresh | late | stale | unknown
    │  degraded_status:  none  | partial | missing | source_unavailable
    ▼
Macro Snapshot  ──────────────────────────────────────────────────────────┐
    │  category states: growth | inflation | labor | policy | fin_conds   │
    │  missing_inputs list                                                 │
    ▼                                                                      │
Quant Scoring Engine  ────────────────────────────────────────────────────┤
    │  5 dimension scores [0.0–1.0]                                        │
    │  breadth · momentum · change_intensity · overall_support            │
    ▼                                                                      │
Regime Classification ◄───────────────────────────────────────────────────┘
    │  label: goldilocks | disinflation | slowdown | ...                  
    │  family: expansion | inflation_transition | late_cycle | ...        
    │  confidence: high | medium | low  (quant-informed, heuristic)       
    │  transition_type: initial | unchanged | shift | weakening | ...     
    ▼
Conflict Detection
    │  conflict_status: clean | tension | mixed | low_conviction
    │  supporting_drivers / conflicting_drivers lists
    │  quant_support_level: strong | moderate | weak | unknown
    ▼
Signal Engine (regime-grounded)
    │  signal_type: buy | sell | hold
    │  strength: strong | moderate | weak
    │  score [0.0–1.0]
    │  is_degraded + caveat (data quality propagation)
    │  conflict surface (analytical conviction)
    ▼
Explanation Builder (deterministic, template-based)
    │  summary · rationale_points · caveats · data_quality_notes
    │  regime_context dict
    ▼
Read-Only API  ←→  Streamlit Analyst Workbench
```

---

## Current capabilities

### ✅ Completed

| Layer | Capability |
|-------|-----------|
| **Data Foundation** | Macro indicator catalog, FRED source mapping, raw payload normalisation, freshness tracking, ingestion run records |
| **Snapshot Layer** | Deterministic category-state derivation, snapshot build/persist, current-vs-prior snapshot comparison |
| **Regime Engine** | 9-label / 6-family regime classification, degraded handling, transition tracking, regime persistence, read API |
| **Quant Scoring Engine v1** | Five dimension scores, breadth/momentum/change-intensity secondaries, `overall_support` aggregate |
| **Confidence Refactor** | Quant-informed regime confidence; signal score adjusted by regime confidence; degraded state propagation |
| **Conflict Surface v1** | `ConflictStatus` enum (clean/tension/mixed/low_conviction), `ConflictSurface` model, `derive_conflict()` function, `is_mixed` convenience flag |
| **Signal Engine** | Regime-grounded rule evaluation, `supporting_drivers` / `conflicting_drivers` per signal, `is_degraded` + `caveat` propagation from regime |
| **Explanation API** | `GET /api/explanations/regime/latest` — deterministic narrative from persisted regime; `GET /api/explanations/{id}` — per-signal explanation retrieval |
| **Analyst API** | Read-only FastAPI routes for snapshots, regimes, signals, explanations, sessions; `trust` metadata on every response |
| **Analyst Workbench** | Streamlit app consuming the REST API; snapshot panel, comparison table, signal cards, trust badges |
| **Observability** | Prometheus metrics, Grafana dashboards, structured logging via `structlog`, OpenTelemetry tracing |

### 🔜 Next (planned — not yet in codebase)

- **Explanation Engine v2** — structured `reasoning_chain` objects replacing template strings; `what_changed` section
- **Explanation Persistence** — durable repository replacing the in-memory `_store` dict
- **Analyst Workflow Surface** — ordered 6-step workflow DTO (current_state → why → confidence → conflict → caveats → what_changed) and updated workbench panels

---

## Trust / state semantics

This is the most important section for API consumers and frontend engineers.

### Degraded vs Mixed — not the same thing

| Concept | What it means | Where it appears |
|---------|--------------|-----------------|
| **Degraded** | An **input problem** — data is stale, incomplete, or from an unavailable source. The snapshot itself is unreliable. | `is_degraded`, `caveat`, `trust.availability`, `trust.degraded_reason` |
| **Mixed / Conflicted** | An **interpretation problem** — macro drivers are analytically contested. The data may be fine; the picture is just ambiguous. | `conflict_status`, `is_mixed`, `conflict_note` |

These are orthogonal. A signal can be:
- **healthy + clean** — fresh data, coherent drivers
- **healthy + conflicted** — fresh data, but growth and policy point in opposite directions
- **degraded + clean** — stale data, but available drivers don't conflict
- **degraded + conflicted** — worst case: both input quality and interpretation are compromised

**UI rule:** render degraded warnings and conflict badges in separate, distinct UI elements. Never conflate them.

### Regime status tokens

`GET /api/regimes/latest` returns a `status` field:

| Value | Meaning |
|-------|---------|
| `success` | Healthy, real (non-synthetic) data, fresh |
| `bootstrap` | Regime built from synthetic startup seed data — not a real ingestion run |
| `stale` | Underlying data is older than expected freshness window |
| `degraded` | Partial indicators, low confidence, or mixed/unclear regime label |

### Signal status tokens

`GET /api/signals/latest` returns a `status` field:

| Value | Meaning |
|-------|---------|
| `success` | Regime-grounded signals derived from healthy regime |
| `degraded` | Regime-grounded but regime itself is degraded/stale/low-confidence |
| `fallback` | No persisted regime — snapshot-based fallback engine used |
| `empty` | No signals generated (empty registry or no-op evaluation) |

### Conflict status vocabulary

| Value | Meaning | Action guidance |
|-------|---------|----------------|
| `clean` | All drivers support the signal direction coherently | Full conviction |
| `tension` | Supporting drivers outnumber conflicting, but some opposition exists | Reduced conviction; monitor conflicting drivers |
| `mixed` | Conflicting and supporting drivers roughly balance out | No directional view; do not act with high conviction |
| `low_conviction` | No supporting drivers, or quant `overall_support < 0.35` | Treat as indicative only |

### Confidence values

`high | medium | low` — derived deterministically from data freshness, degraded status, quant scores, and category state coherence. See `docs/regime_confidence_policy.md` for full rules.

**Important:** Confidence is heuristic, not statistically calibrated. The quant score multipliers are intentionally conservative. Do not treat `high` confidence as equivalent to a probability estimate.

### Bootstrap / synthetic data

On startup, the application seeds the in-memory regime and snapshot stores with synthetic observations. This ensures the API is functional from the first request.

Bootstrap data is **clearly marked** on every response:
- `RegimeLatestResponse.is_seeded == true`
- `RegimeLatestResponse.data_source == "synthetic_seed"`
- `ExplanationResponse.data_quality_notes` includes a bootstrap warning

Production deployments should disable the seeder (`SEED_ON_STARTUP=false`) and rely on real ingestion pipeline runs.

---

## API surface overview

All routes are **read-only**. No write endpoints are exposed.

| Method | Route | Description | Status |
|--------|-------|-------------|--------|
| `GET` | `/health` | Liveness probe | Stable |
| `GET` | `/readiness` | Readiness probe (includes seed state) | Stable |
| `GET` | `/metrics` | Prometheus scrape endpoint | Stable |
| `GET` | `/api/snapshots/latest` | Latest macro snapshot for a country | Stable |
| `POST` | `/api/snapshots/compare` | Current vs prior snapshot delta | Stable |
| `GET` | `/api/regimes/latest` | Latest persisted macro regime | Stable |
| `GET` | `/api/regimes/compare` | Current vs prior regime transition | Stable |
| `GET` | `/api/signals/latest` | Latest regime-grounded signal evaluations | Phase 3 bridge |
| `GET` | `/api/explanations/regime/latest` | Analyst narrative for current regime | Phase 3 bridge |
| `GET` | `/api/explanations/{id}` | Explanation by run/signal ID (in-memory) | Experimental |
| `GET` | `/api/sessions/{id}` | Session context by ID | Experimental |

Interactive API docs: `http://localhost:8000/docs`

---

## Quick start

### Prerequisites

- Python ≥ 3.12
- [uv](https://github.com/astral-sh/uv) (package manager)
- Docker + Docker Compose

### 1. Install dependencies

```bash
uv sync --all-extras
```

### 2. Start local services (Postgres, Prometheus, Grafana)

```bash
docker compose up -d
```

### 3. Start the API server

```bash
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start the analyst workbench (optional)

```bash
streamlit run apps/workbench/app.py
```

### 5. Key URLs

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Liveness | http://localhost:8000/health |
| Readiness | http://localhost:8000/readiness |
| Analyst workbench | http://localhost:8501 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

### 6. Run tests

```bash
pytest
```

---

## Example responses

### `GET /api/regimes/latest`

```json
{
  "regime_id": "reg-abc123",
  "as_of_date": "2026-04-19",
  "regime_label": "goldilocks",
  "regime_family": "expansion",
  "confidence": "high",
  "freshness_status": "fresh",
  "degraded_status": "none",
  "missing_inputs": [],
  "supporting_states": {
    "growth_state": "accelerating",
    "inflation_state": "cooling",
    "labor_state": "stable",
    "policy_state": "neutral",
    "financial_conditions_state": "accommodative"
  },
  "transition": {
    "transition_from_prior": "slowdown",
    "transition_type": "shift",
    "changed": true
  },
  "rationale_summary": "Growth accelerating, inflation cooling, policy neutral — classic Goldilocks conditions.",
  "warnings": [],
  "status": "success",
  "is_seeded": false,
  "data_source": "fred"
}
```

### `GET /api/signals/latest`

```json
{
  "country": "US",
  "run_id": "run-xyz789",
  "regime_label": "goldilocks",
  "as_of_date": "2026-04-19",
  "is_regime_grounded": true,
  "status": "success",
  "signals_count": 2,
  "buy_count": 2,
  "sell_count": 0,
  "hold_count": 0,
  "signals": [
    {
      "signal_id": "equities_overweight",
      "signal_type": "buy",
      "strength": "strong",
      "score": 0.85,
      "asset_class": "equities",
      "supporting_regime": "goldilocks",
      "supporting_drivers": ["growth_accelerating", "inflation_cooling"],
      "conflicting_drivers": ["policy_restrictive"],
      "is_degraded": false,
      "caveat": null,
      "conflict_status": "tension",
      "is_mixed": false,
      "conflict_note": "Signal direction supported (2 factors) but 1 conflicting driver reduces conviction. Quant support: strong.",
      "quant_support_level": "strong"
    }
  ],
  "trust": {
    "freshness_status": "fresh",
    "availability": "full",
    "is_degraded": false
  }
}
```

### `GET /api/explanations/regime/latest`

```json
{
  "explanation_id": "regime:reg-abc123",
  "run_id": "reg-abc123",
  "signal_id": null,
  "summary": "The macro environment is in a Goldilocks regime... Regime confidence is HIGH...",
  "rationale_points": [
    "Regime: goldilocks (family: expansion)",
    "As of date: 2026-04-19",
    "Growth: accelerating",
    "Inflation: cooling",
    "Labour: stable",
    "Policy: neutral",
    "Financial Conditions: accommodative",
    "Confidence: high",
    "Transition from prior: slowdown (shift)"
  ],
  "caveats": [],
  "data_quality_notes": [],
  "regime_label": "goldilocks",
  "regime_context": {
    "label": "goldilocks",
    "family": "expansion",
    "confidence": "high",
    "transition": "shift",
    "freshness": "fresh",
    "degraded_status": "none"
  },
  "generated_at": "2026-04-19T18:00:00+00:00",
  "trust": {
    "freshness_status": "fresh",
    "availability": "full",
    "is_degraded": false
  }
}
```

---

## Repository structure

```
macro-invest-agent-system/
│
├── domain/                         # Deterministic business logic (no I/O)
│   ├── macro/                      # Snapshot, regime, narrative builder
│   │   ├── models.py               # MacroFeature, MacroSnapshot
│   │   ├── regime.py               # RegimeLabel, RegimeFamily, MacroRegime
│   │   ├── regime_mapping.py       # Snapshot → regime classification
│   │   ├── regime_transition.py    # Transition type derivation
│   │   ├── snapshot.py             # DegradedStatus, snapshot state derivation
│   │   └── narrative_builder.py    # Deterministic regime explanation builder
│   ├── quant/                      # Quant Scoring Engine v1
│   │   ├── models.py               # DimensionScore, QuantScoreBundle
│   │   └── scoring.py              # Score derivation from snapshot states
│   └── signals/                    # Signal engine and conflict surface
│       ├── models.py               # SignalOutput, SignalResult
│       ├── engine.py               # Deterministic rule evaluator
│       ├── conflict.py             # ConflictSurface, derive_conflict()
│       ├── regime_signal_rules.py  # RegimeLabel → signal rule mappings
│       └── registry.py             # In-memory signal definition registry
│
├── services/                       # Orchestration layer (thin, async-first)
│   ├── interfaces.py               # Abstract service contracts
│   ├── macro_service.py            # Macro data fetch/snapshot coordination
│   ├── macro_snapshot_service.py   # Snapshot build and persist
│   ├── macro_regime_service.py     # Regime persist and read
│   ├── quant_scoring_service.py    # Quant score computation wrapper
│   └── signal_service.py          # Signal engine orchestration
│
├── apps/
│   ├── api/                        # FastAPI analyst-facing read API
│   │   ├── main.py                 # App entry point, lifespan, routes
│   │   ├── routers/                # Route handlers (snapshots, regimes, signals, explanations)
│   │   ├── dto/                    # Frontend-friendly response contracts
│   │   │   ├── trust.py            # TrustMetadata, FreshnessStatus, DataAvailability
│   │   │   ├── explanations.py     # ExplanationResponse
│   │   │   └── builders.py         # Domain → DTO pure translation functions
│   │   ├── dependencies.py         # FastAPI DI wiring
│   │   └── startup_seeder.py       # Synthetic bootstrap data for dev/test
│   └── workbench/                  # Streamlit analyst workbench
│       ├── app.py                  # Workbench entry point
│       └── components/             # Snapshot panel, comparison table, signal cards, trust badges
│
├── pipelines/                      # Data ingestion and normalization workflows
│   └── ingestion/                  # Prefect pipelines, FRED adapter, freshness logic
│
├── adapters/                       # External data source adapters (FRED, etc.)
├── storage/                        # Repository interfaces and implementations
├── alembic/                        # Database migrations
├── core/                           # Config, logging, tracing
├── mcp/                            # MCP tool handlers and schemas (agent interface)
├── tests/                          # Unit and integration tests (pytest)
├── evals/                          # Evaluation harness for signal quality
├── docs/                           # Architecture, contracts, runbooks, roadmap
├── deploy/                         # Deployment configuration
├── docker-compose.yml
└── pyproject.toml
```

---

## Architecture principles

### 1. Determinism is the contract

The signal engine, regime classifier, narrative builder, and conflict derivation function produce **identical outputs for identical inputs**. No randomness, no timestamp-dependent branching, no external calls during evaluation. This makes every output auditable and every test reproducible.

### 2. Domain layer has no I/O

`domain/` contains pure computation — no database calls, no HTTP, no file system access. Services (`services/`) orchestrate I/O and call domain functions. This boundary is enforced by convention and tested.

### 3. Typed schemas at all boundaries

All domain models, service interfaces, and API DTOs use Pydantic v2 with full type annotations. Validation happens at model construction time. The product DTO layer (`apps/api/dto/`) is separate from domain models — the API contract is stable even when internal domain models evolve.

### 4. Trust metadata is first-class

Every API response carries a `trust` block that exposes `freshness_status`, `availability`, `is_degraded`, and `degraded_reason` so that frontend consumers can render appropriate warnings without any domain knowledge.

### 5. Degrade gracefully, surface honestly

When data is stale, incomplete, or synthetic, the platform does not silently return a misleading output. Every degraded path has a distinct `status` token, a `caveat` string, and a `degraded_reason` machine code. Analysts see exactly what the system knows and does not know.

### 6. Separate degraded (data) from mixed (interpretation)

Data quality problems and analytical uncertainty are tracked independently. The two must never be conflated in code or in the UI. See [Trust / state semantics](#trust--state-semantics) above.

---

## Known limitations

These are intentional constraints in the current codebase — not bugs or oversights.

| Limitation | Details |
|-----------|---------|
| **In-memory persistence** | Regime and snapshot stores are in-memory. Explanation store is in-memory. All data is lost on restart unless re-seeded. Durable persistence is deferred. |
| **Heuristic confidence only** | `high / medium / low` confidence is derived from deterministic rules, not from a statistically calibrated model. The quant score multipliers are conservative heuristics. |
| **Template-based explanations** | Current narratives are built from fixed templates per regime label + confidence. They do not reflect real-time indicator deltas or adapt to unusual state combinations. |
| **No LLM generation** | All explanation and narrative generation is deterministic and template-based. LLM-backed explanation augmentation is explicitly deferred. |
| **Conflict engine v1 uses driver counts** | Conflict status is derived from raw counts of supporting vs conflicting drivers, not from a weighted cross-asset model. |
| **Bootstrap data in dev** | The startup seeder populates stores with synthetic data. This is sufficient for development and demos; it is not a production-grade data pipeline run. |
| **Signal definitions are rule-based** | Signal rules use condition strings evaluated deterministically. Dynamic signal confidence (adjusting for real-time indicator recency) is deferred. |
| **Freshness always "fresh" for live-fetched snapshots** | Staleness detection requires a configurable max-age policy per indicator frequency — not yet implemented. |
| **No cross-asset ensemble** | Under `GOLDILOCKS`, equities may be `BUY` while bonds are `HOLD`. No ensemble engine reconciles multi-asset disagreements yet. |

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** — Macro Data Foundation | ✅ Complete | Indicator catalog, FRED ingestion, normalisation, freshness |
| **Phase 2** — Macro Snapshot Layer | ✅ Complete | Category-state derivation, snapshot comparison |
| **Phase 3** — Macro Regime Engine | ✅ Complete | Regime classification, confidence, transition, API |
| **Active bridge work** | 🔄 Complete | Quant Scoring Engine v1, Confidence Refactor, Conflict Surface v1 |
| **Next** — Explanation Engine v2 | 🔜 Planned | Structured reasoning objects, `reasoning_chain`, `what_changed` |
| **Next** — Explanation Persistence | 🔜 Planned | Durable repository replacing in-memory store; Alembic migration |
| **Next** — Analyst Workflow Surface | 🔜 Planned | 6-step `analyst_workflow` DTO; updated workbench panels; conflict badge |
| **Phase 4** — Multi-Engine Hub | ⏳ Future | Cross-asset signal engine, risk/conflict ensemble engine |
| **Phase 5** — AI Explanation Engine | ⏳ Future | LLM-backed explanation augmentation (separate from deterministic core) |
| **Phase 6+** — Conversational analyst | ⏳ Future | Multi-turn analyst dialog, agent orchestration |

---

## Development and contribution notes

### Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| API framework | FastAPI |
| Data validation | Pydantic v2 |
| Package manager | uv |
| Workflow orchestration | Prefect |
| Analyst workbench | Streamlit |
| Observability | Prometheus + Grafana + OpenTelemetry |
| Testing | pytest + pytest-asyncio + httpx TestClient |
| Linting | ruff |
| Type checking | mypy (strict) |

### Development workflow

1. **Domain first** — define or update Pydantic models in `domain/` before writing service or API code.
2. **Tests alongside** — write unit tests for domain logic and DTO builders; use `InMemoryRepository` implementations for route tests.
3. **Contract tests** — `tests/unit/api/test_product_surface_contract.py` asserts trust block presence and status semantics across all response types. Add assertions here when adding new status codes or fields.
4. **Semantic discipline** — never conflate `is_degraded` (data quality) with `is_mixed` / `conflict_status` (analytical tension) in any code path or test.
5. **No silent no-ops** — if a persistence operation is called, it must actually persist. In-memory stores are acceptable in dev; fake success returns are not.

### Adding a new regime label

1. Add to `RegimeLabel` in `domain/macro/regime.py`
2. Add to `REGIME_LABEL_FAMILY_MAP`
3. Add mapping rules in `domain/macro/regime_mapping.py`
4. Add narrative template in `domain/macro/narrative_builder.py` (`_LABEL_SUMMARY`)
5. Add signal rules in `domain/signals/regime_signal_rules.py`
6. Update tests in `tests/unit/domain/`

### Adding a new data source

1. Extend `MacroSourceType` enum in `domain/macro/enums.py`
2. Implement a new adapter in `adapters/`
3. Wire into the ingestion pipeline in `pipelines/ingestion/`
4. No changes required in the domain or API layers

---

## Canonical documentation index

| Document | Purpose |
|----------|---------|
| `docs/architecture.md` | Architecture overview |
| `docs/roadmap.md` | Phase roadmap and deferred work |
| `docs/regime_engine.md` | Regime engine docs index |
| `docs/regime_confidence_policy.md` | Confidence derivation rules |
| `docs/conflict_surface_v1.md` | Conflict surface semantics and API contract |
| `docs/snapshot_schema.md` | Snapshot contract |
| `docs/state_derivation_rules.md` | Category-state derivation logic |
| `docs/macro_indicator_catalog.md` | Macro indicator definitions |
| `docs/ingestion_design.md` | Ingestion flow and normalization |
| `docs/storage_schema.md` | Storage schema and rules |
| `docs/freshness_policy.md` | Freshness classification rules |
| `docs/legacy_surface_status.md` | API surface maturity and bootstrap data policy |
| `docs/phase6_analyst_surface.md` | Analyst API and workbench contract details |
| `docs/ci_cd.md` | CI/CD guide |
| `docs/metrics.md` | Prometheus metrics reference |
| `docs/deployment.md` | Deployment guide |
| `docs/runbooks/README.md` | Operational runbook index |
