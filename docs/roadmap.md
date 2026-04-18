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

### Upcoming Phase 4 work

Phase 4 = **Multi-Engine Analysis Hub** (not yet started):

- Quant Scoring Engine
- Cross-Asset Signal Engine
- Risk / Conflict Engine
- AI Explanation Engine (LLM-backed)
- Ensemble / Consensus Engine

Phase details should be refined in backlog tasks, not duplicated in README.
