# Phase 6 — Analyst Experience and Visual Surface

> Analyst-facing read API, frontend-friendly DTOs, trust metadata, structured
> comparison/signal views, and a minimal Streamlit workbench.

---

## Overview

Phase 6 turns the existing deterministic macro + signal + MCP + agent platform
into a usable analyst-facing product surface.

The primary artefacts are:

| Layer | Module | Purpose |
|-------|--------|---------|
| **Product API** | `apps/api/routers/` | Read-only FastAPI routes for analyst reads |
| **Product DTOs** | `apps/api/dto/` | Frontend-friendly typed response contracts |
| **Trust metadata** | `apps/api/dto/trust.py` | Freshness, degraded, source-attribution fields |
| **DTO builders** | `apps/api/dto/builders.py` | Domain → DTO translation (pure, no side effects) |
| **Dependencies** | `apps/api/dependencies.py` | FastAPI DI wiring for service injection |
| **Workbench** | `apps/workbench/` | Minimal Streamlit visual surface |
| **Tests** | `tests/unit/api/` | Route, DTO, trust, and contract tests |

---

## API Route Summary

All routes are **read-only**. No mutations are exposed.

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/readiness` | Readiness probe |
| `GET` | `/metrics` | Prometheus scrape endpoint |
| `GET` | `/api/snapshots/latest` | Latest macro snapshot for a country |
| `POST` | `/api/snapshots/compare` | Compare current vs prior snapshot |
| `GET` | `/api/signals/latest` | Latest signal evaluations for a country |
| `GET` | `/api/explanations/{id}` | Explanation by run/signal ID |
| `GET` | `/api/sessions/{id}` | Session context by ID |

Interactive docs: `http://localhost:8000/docs`

---

## DTO Contract Summary

### `SnapshotLatestResponse`

```json
{
  "country": "US",
  "features_count": 3,
  "features": [
    {
      "indicator_type": "gdp",
      "indicator_label": "GDP Growth",
      "value": 3.2,
      "source_id": "fred",
      "frequency": "quarterly",
      "country": "US",
      "observed_at": "2026-01-15T12:00:00+00:00"
    }
  ],
  "trust": { ... }
}
```

### `SnapshotCompareResponse`

```json
{
  "country": "US",
  "prior_snapshot_label": "Q1-2026",
  "changed_count": 2,
  "unchanged_count": 0,
  "no_prior_count": 1,
  "deltas": [
    {
      "indicator_type": "gdp",
      "indicator_label": "GDP Growth",
      "current_value": 3.2,
      "prior_value": 3.0,
      "delta": 0.2,
      "direction": "increased",
      "is_significant": false
    }
  ],
  "trust": { ... }
}
```

Possible `direction` values: `"increased"`, `"decreased"`, `"unchanged"`, `"no_prior"`.

### `SignalsLatestResponse`

```json
{
  "country": "US",
  "run_id": "run-abc123",
  "signals_count": 1,
  "buy_count": 1,
  "sell_count": 0,
  "hold_count": 0,
  "strongest_signal_id": "bull_market",
  "signals": [
    {
      "signal_id": "bull_market",
      "signal_type": "buy",
      "strength": "strong",
      "score": 0.85,
      "trend": "up",
      "rationale": "GDP positive and inflation contained.",
      "triggered_at": "2026-01-15T12:00:00+00:00",
      "rule_results": { "gdp_growth_positive": true, "inflation_contained": true },
      "rules_passed": 2,
      "rules_total": 2
    }
  ],
  "trust": { ... }
}
```

### `ExplanationResponse`

```json
{
  "explanation_id": "run-abc123:bull_market",
  "run_id": "run-abc123",
  "signal_id": "bull_market",
  "summary": "Bull market conditions confirmed.",
  "rationale_points": ["GDP > 2%", "Inflation < 4%"],
  "generated_at": "2026-01-15T12:00:00+00:00",
  "trust": { ... }
}
```

### `SessionResponse`

```json
{
  "session_id": "sess-001",
  "created_at": "2026-01-15T10:00:00+00:00",
  "updated_at": "2026-01-15T12:00:00+00:00",
  "country": "US",
  "request_count": 3,
  "request_ids": ["req-1", "req-2", "req-3"],
  "trust": { ... }
}
```

---

## Trust Metadata

Every response includes a `trust` block:

```json
{
  "snapshot_timestamp": "2026-01-15T12:00:00+00:00",
  "previous_snapshot_timestamp": null,
  "freshness_status": "fresh",
  "availability": "full",
  "is_degraded": false,
  "sources": [
    {
      "source_id": "fred",
      "source_label": "FRED — Federal Reserve",
      "retrieval_timestamp": "2026-01-15T12:00:00+00:00"
    }
  ],
  "changed_indicators_count": null
}
```

### `freshness_status` values

| Value | Meaning |
|-------|---------|
| `"fresh"` | Data is within expected update window |
| `"stale"` | Data is older than the expected window |
| `"unknown"` | Freshness could not be determined |

### `availability` values

| Value | Meaning |
|-------|---------|
| `"full"` | All expected data is present |
| `"partial"` | Some data is present; some is missing |
| `"degraded"` | Data available but below quality threshold |
| `"unavailable"` | No data could be retrieved |

---

## Workbench

The minimal analyst workbench is a Streamlit application at `apps/workbench/app.py`.

```bash
streamlit run apps/workbench/app.py
```

### Components

| Component | Module | Description |
|-----------|--------|-------------|
| Snapshot panel | `components/snapshot_panel.py` | Metric grid of macro indicator values |
| Comparison table | `components/comparison_table.py` | Before/after delta table with direction icons |
| Signal panel | `components/signal_panel.py` | Expandable signal cards with scores and rule results |
| Trust badges | `components/trust_badges.py` | Freshness, availability, and source badges |
| States | `components/states.py` | Loading, empty, and error state helpers |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | FastAPI base URL |

---

## Test Coverage Summary

| Test file | What it covers |
|-----------|---------------|
| `test_snapshots_router.py` | Latest snapshot and comparison routes (success + failure paths) |
| `test_signals_router.py` | Signal evaluation route (success + error paths, type filtering) |
| `test_explanations_router.py` | Explanation retrieval (found, not found, composite IDs) |
| `test_sessions_router.py` | Session retrieval (found, not found, field semantics) |
| `test_trust_dto.py` | DTO builders, trust metadata field semantics, enum values |
| `test_contract.py` | Edge states: trust block presence, empty, partial, degraded, unavailable |

---

## Design Decisions and Tradeoffs

### Product DTOs are separate from domain models

Domain models (`domain/macro/models.py`, `domain/signals/models.py`) are never
exposed directly through the product API. The `apps/api/dto/builders.py`
module translates domain objects to DTOs. This:
- Stabilises the product contract independently of internal refactors
- Allows frontend-optimised field naming and label fields
- Prevents accidental leakage of internal implementation details

### In-memory stores for explanations and sessions (Phase 6 MVP)

The explanation and session stores use in-memory dicts in the Phase 6 MVP.
This is sufficient for demos and internal analyst validation.
Future work: replace with repository-backed persistence (see `storage/repositories/`).

### Freshness is always "fresh" for live-fetched snapshots (Phase 6 MVP)

Stale detection requires a configurable maximum-age policy per indicator frequency.
This is deferred to a future enhancement. The `freshness_status` field is in
the DTO contract so the UI is ready to render stale badges without a schema change.

### Workbench consumes the FastAPI API, not domain services directly

All workbench data flows through the REST API. This:
- Validates the API contracts end-to-end
- Keeps the workbench aligned with what any external consumer would receive
- Makes it easy to test the API independently of the workbench

---

## Deferred Follow-ups

- [ ] Repository-backed persistence for explanations and sessions
- [ ] Staleness detection with configurable max-age per frequency
- [ ] Pagination for snapshot feature lists and signal lists
- [ ] Explanation workbench panel (GET /api/explanations/{id} view in workbench)
- [ ] Signal filtering by type in the workbench sidebar
- [ ] Write integration tests against a live server (not just TestClient)
