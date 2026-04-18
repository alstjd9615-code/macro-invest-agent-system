# Legacy Surface Status

This document tracks active product surfaces and their current state.

---

## Experimental surfaces (active)

1. `GET /api/signals/latest`
   - Status: **Regime-grounded (Phase 3 bridge)**
   - Behaviour: when a persisted regime is available, signals are derived
     deterministically from the regime label via the Rule-Based Macro Engine.
     When no regime is available, falls back to the snapshot-based engine and
     returns `trust.availability = "degraded"` with
     `trust.degraded_reason = "regime_unavailable_fallback_engine_used"`.

2. `GET /api/explanations/{id}`
   - Status: **Experimental**
   - Reason: signal-level explanation retrieval is in-memory; not a finalized
     persisted explanation workflow.

3. `GET /api/explanations/regime/latest`
   - Status: **Phase 3 bridge (active)**
   - Behaviour: returns structured analyst-facing narrative for the latest
     persisted regime, including `summary`, `rationale_points`, `caveats`,
     `data_quality_notes`, and `regime_context` (with minimum documented keys:
     `label`, `family`, `confidence`, `transition`, `freshness`, `degraded_status`).

4. Frontend signals/explanations sections
   - Status: **Experimental**
   - Reason: these sections render the regime-grounded signal/explanation APIs
     which are in Phase 3 bridge, not Phase 4 finalized.

---

## Bootstrap / Startup Seeder data policy

The API uses a **startup seeder** (`apps/api/startup_seeder.py`) to populate
the in-memory regime and snapshot stores with synthetic data at application
boot.

**Bootstrap data characteristics:**

| Property | Value |
|---|---|
| Data type | Synthetic / dev bootstrap |
| Source | `apps/api/startup_seeder.py` |
| Identification | `regime.metadata["seeded"] == "true"` |
| API surface | `RegimeLatestResponse.is_seeded == true`, `data_source == "synthetic_seed"` |
| Freshness | Marked `FRESH` (synthetic observations created at boot time) |
| Idempotency | Seeder skips if regime store is already populated |
| Failure policy | Non-blocking: seeder failure logs a warning; app continues; `GET /readiness` exposes `seed_status: "degraded:<reason>"` |

**Consumer guidance:**

- `GET /api/regimes/latest` returns HTTP 200 after startup, but the response
  will carry `is_seeded: true` and `data_source: "synthetic_seed"` until a
  real ingestion pipeline run populates the store.
- `GET /api/explanations/regime/latest` will include a `data_quality_notes`
  entry noting "Bootstrap data: this regime was generated from synthetic seed data".
- Production deployments should run a real ingestion pipeline on startup and
  disable or gate the seeder behind a feature flag.

---

## Non-experimental current core

- Ingestion foundation (Phase 1)
- Snapshot contract/derivation/comparison (Phase 2)
- Regime contract/mapping/confidence/transition/persistence/read API (Phase 3)

## Cleanup policy

- Keep experimental surfaces visible only with explicit experimental labeling.
- Bootstrap data is not production data. Mark it explicitly in all API responses.
- Degraded state (`availability = "degraded"`) must be surfaced with a
  machine-readable `degraded_reason` so frontend can render appropriate UI state.

- Do not present experimental outputs as production-grade inference.
- Prefer narrowing labels and scope over feature expansion.
