# Roadmap

## Phase 1 — Macro Data Foundation ✅

Objective: build reliable ingestion + normalization for priority macro indicators.

Primary deliverables:

- indicator catalog
- source mapping
- raw payload handling
- normalized observation schema
- ingestion run tracking
- freshness baseline

## Phase 2 — Macro Snapshot Layer ✅

- Snapshot contract
- Deterministic category-state derivation
- Snapshot build/persist
- Current-vs-previous snapshot comparison

## Phase 3 — Macro Regime Engine ✅ (baseline complete)

- Regime schema/contract
- Snapshot-to-regime deterministic mapping
- Regime confidence/degraded handling
- Regime transition comparison
- Regime persistence and read API contract
- Canonical docs index: `docs/regime_engine.md`

---

## Active Workstream — Multi-Engine Analysis Hub

**Current phase focus: Phase 3 completion → Phase 4 bridge**

This workstream extends Phase 3 with the signal and explanation layers that
complete the analyst-facing chain:

```
Snapshot → Regime → Signals → Explanations → API/UI
```

### Phase 3 bridge work (in progress)

- **Startup regime seeder** — synthetic bootstrap data for dev/test;
  idempotent, metadata-stamped, non-blocking on failure.
  See `docs/legacy_surface_status.md` for bootstrap data policy.
- **Regime-grounded signal rules** — deterministic `RegimeLabel → signals`
  mapping with structured `asset_class`, `signal_direction`, `signal_strength`,
  `signal_confidence`, `supporting_drivers`, `conflicting_drivers`.
- **Structured narrative explanations** — analyst-facing `summary`,
  `rationale_points`, `caveats`, `data_quality_notes`, `regime_context`
  surfaced via `GET /api/explanations/regime/latest`.
- **Regime backbone hardening** — `warnings` field on `MacroRegime` domain
  model; `derive_regime_warnings()` helper; `status` and `warnings` on
  `RegimeLatestResponse`; `current_rationale_summary`, `warnings`, `is_seeded`
  on `RegimeCompareResponse`.  See contract notes below.
- **Signal Engine v2 alignment** — `is_degraded` and `caveat` on `SignalOutput`
  and `SignalSummaryDTO`; regime degraded state propagated to every signal;
  `regime_label`, `as_of_date`, `is_regime_grounded`, `status` on
  `SignalsLatestResponse`.  Signal `status` values: `success`, `degraded`,
  `fallback`, `empty`.
- **Product surface & UX contract alignment** — explicit `status` fields on
  regime and signal responses; `_compute_regime_status()` helper; cross-endpoint
  contract tests.  See `tests/unit/api/test_product_surface_contract.py`.

### API/UI contract notes

#### Regime response `status` field
`GET /api/regimes/latest` now includes a top-level `status` field:
- `"success"` — healthy, non-synthetic, fresh data
- `"bootstrap"` — regime built from synthetic startup seed data
- `"stale"` — underlying data older than expected freshness window
- `"degraded"` — partial indicators, low confidence, or mixed/unclear regime

#### Signal response `status` field
`GET /api/signals/latest` now includes `status`, `is_regime_grounded`,
`regime_label`, and `as_of_date`:
- `"success"` — healthy regime-grounded signals
- `"degraded"` — regime-grounded but regime is degraded/stale/low-confidence
- `"fallback"` — no persisted regime, snapshot-based fallback engine used
- `"empty"` — no signals generated

#### Signal degraded propagation
When the grounding regime is degraded/stale/bootstrap, every derived signal
receives `is_degraded=True` and a `caveat` string explaining the specific
condition.  Caveat priority order:
1. bootstrap/seeded
2. mixed/unclear (non-directional)
3. stale freshness
4. unknown freshness
5. missing/source-unavailable degraded status
6. partial degraded status
7. low confidence

### Upcoming Phase 4 work

Phase 4 = **Multi-Engine Analysis Hub** (not yet started):

- Quant Scoring Engine
- Cross-Asset Signal Engine
- Risk / Conflict Engine
- AI Explanation Engine (LLM-backed)
- Ensemble / Consensus Engine

Phase details should be refined in backlog tasks, not duplicated in README.

---

## Known Limitations / Deferred Work

These items are intentionally out of scope for the current v1 delivery and
are tracked here to prevent silent omission.  Each item is linked to a
future phase where it will be addressed.

### Phase 4–5
- **Dynamic signal confidence** — `signal_confidence` is currently hard-coded at
  the rule layer.  In a later phase it should be dynamically adjusted using regime
  confidence, indicator recency/freshness, missing/degraded inputs, and quant
  scoring outputs.
- **Cross-asset conflict resolution** — under `GOLDILOCKS`, equities may be `BUY`
  while bonds remain `HOLD`.  A dedicated Conflict / Ensemble Engine is needed to
  reconcile multi-asset disagreements and downgrade conviction where signals conflict.
- **Richer signal rationale** — current rationale is template-based.  A richer
  signal-level narrative that reflects real-time indicator deltas is deferred to
  the Quant Scoring Engine phase.

### Phase 5
- **Explanation persistence** — explanation generation remains in-memory in v1.
  Follow-up work should add persistence for auditability, reproducibility, and
  historical explanation retrieval.
- **Better narrative quality** — narrative templates will be expanded and improved
  as more regime/signal data becomes available.

### Phase 5–6
- **LLM-backed explanation** — current explanation logic is deterministic and
  template-based.  Replacing or augmenting this with an LLM-backed AI Explanation
  Engine is future work.
- **Conversational explanation** — multi-turn analyst dialog is a Phase 6+
  capability.

### Phase 7
- **Production-safe seeding controls** — startup seeding is controlled by the
  `SEED_ON_STARTUP` environment variable (default `True`).  A full feature-flag
  system with per-environment defaults, audit trail, and remote toggle is Phase 7
  work.
- **Persistence and audit trail** — the in-memory regime/snapshot stores must be
  backed by a durable repository before production deployment.
