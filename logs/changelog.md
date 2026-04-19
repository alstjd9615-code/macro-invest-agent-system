# Changelog

## 2026-04-19

### Added
- **Quant Scoring Engine v1** (`domain/quant/`): deterministic per-dimension scoring
  for growth, inflation, labor, policy, and financial conditions.  Produces a
  `QuantScoreBundle` with primary dimension scores and secondary measures
  (`breadth`, `momentum`, `change_intensity`, `overall_support`).
- **`QuantScoringService`** (`services/quant_scoring_service.py`): thin, stateless
  wrapper for composable injection.
- **Confidence Refactor**: `derive_regime_confidence()` now accepts an optional
  `QuantScoreBundle` and applies quant-informed downgrade rules (breadth < 0.60
  caps at MEDIUM; overall_support < 0.40 downgrades one level).
- **`MacroRegime.quant_scores`**: regimes built by `MacroRegimeService.build_regime()`
  now carry the quant bundle for downstream consumers.
- **Signal score adjustment** (`_adjust_signal_score()`): signal scores are now
  modulated by regime confidence (HIGH=1.0×, MEDIUM=0.85×, LOW=0.65×) and weak
  quant support (additional 0.85× when overall_support < 0.35).
- **Conflict Surface v1** (`domain/signals/conflict.py`): explicit, deterministic
  `ConflictStatus` (`clean | tension | mixed | low_conviction`) and
  `ConflictSurface` model.  Populated on every regime-grounded signal.
- **Conflict fields in API DTO**: `SignalSummaryDTO` now exposes
  `conflict_status`, `is_mixed`, `conflict_note`, `quant_support_level`.
- 88 new unit tests (33 quant, 22 confidence, 33 conflict); total: 875.
- New docs: `docs/conflict_surface_v1.md`, `docs/backlog/0403-quant-confidence-conflict.md`.
- Updated `docs/regime_confidence_policy.md` with quant adjustment rules,
  signal confidence derivation, and degraded/mixed distinction.

### Changed
- `domain/signals/models.py`: added `conflict: ConflictSurface | None` to
  `SignalOutput` (default `None`; backward compatible).
- `apps/api/dto/signals.py`: added conflict fields to `SignalSummaryDTO`
  (all default to safe values; backward compatible).
- `apps/api/dto/builders.py`: `signal_output_to_dto()` maps conflict fields.
- `services/signal_service.py`: `run_regime_grounded_engine()` now derives
  and attaches a `ConflictSurface` per signal.


### Added
- Added `.github/copilot-instructions.md` to define a reusable backlog-autopilot agent procedure for this repository.
- Added Phase 1 indicator catalog and ingestion job definitions for a priority starter set.
- Added Phase 1 normalization and ingestion-run tracking models.
- Added `docs/phase1_macro_data_foundation.md`.
- Added Phase 2 snapshot contract, builder service, in-memory snapshot repository, and comparison metadata baseline.
- Added canonical docs: `docs/snapshot_schema.md`, `docs/state_derivation_rules.md`.
- Added Phase 3 regime schema contracts and canonical regime schema doc.
- Added canonical regime vocabulary reference doc (`docs/regime_vocabulary.md`).
- Added deterministic snapshot-to-regime mapping rules and mapping tests.
- Added canonical mapping rules doc (`docs/regime_mapping_rules.md`).
- Added deterministic regime confidence and missing-input handling utilities.
- Added canonical confidence policy doc (`docs/regime_confidence_policy.md`).
- Added regime builder service for as-of-date regime construction from snapshots.
- Added canonical regime builder doc (`docs/regime_builder.md`).
- Added macro regime persistence contract and in-memory adapter with latest retrieval.
- Added canonical regime persistence doc (`docs/regime_persistence.md`).
- Added deterministic regime transition logic and transition service wiring.
- Added canonical regime transition rules doc (`docs/regime_transition_rules.md`).
- Added regime API DTOs and read routes (`/api/regimes/latest`, `/api/regimes/compare`).
- Added canonical regime API contract doc (`docs/regime_api_contract.md`).
- Added canonical Phase 3 regime docs index (`docs/regime_engine.md`).
- Added Phase 3 end-to-end regime flow test coverage.
- Added canonical legacy surface status doc (`docs/legacy_surface_status.md`).
- Added GitHub Actions CI workflow (`.github/workflows/ci.yml`).
- Added GitHub Actions CD workflow (`.github/workflows/cd.yml`).
- Added CI/CD quick guide (`docs/ci_cd.md`).

### Changed
- Updated default ingestion indicators to a focused Phase 1 starter set.
- Expanded FRED series mappings for Phase 1 categories and priority indicators.
- Extended in-memory feature store to persist raw payload records, normalized observations, and run metadata.
- Added ingestion throughput metric for raw vs normalized record volumes.
- Expanded Phase 1 storage schema draft to include raw payload, normalized observation, and ingestion run tables.
- Reorganized docs to policy-aligned canonical structure (`architecture`, `roadmap`, `macro_indicator_catalog`, `ingestion_design`, `storage_schema`, `freshness_policy`).
- Simplified README into entry-level quickstart + canonical-doc links.
- Added deterministic regime label-to-family mapping and contract-level enforcement for label/family consistency.
- Updated storage schema docs with Phase 3 regime layer note.
- Simplified README regime references to index link for lower duplication.
- Updated API/UI wording to mark signal/explanation surfaces as experimental.
- Updated snapshot API wording toward observation-table semantics.
- Corrected deployment docs to reflect containerized API/frontend services.
- Updated README/roadmap status wording for post-Phase-3 baseline state.
- Updated frontend dashboard to surface Phase 3 regime latest/transition panels while keeping signals/explanations explicitly experimental.
- Updated README canonical docs links to include CI/CD quick guide.

### Ops
- Added `.github/workflows/copilot-setup-steps.yml` so Copilot cloud agent consistently provisions Python 3.12 + `uv` and installs dependencies before task execution.
