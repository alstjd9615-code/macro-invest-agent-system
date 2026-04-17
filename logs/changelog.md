# Changelog

## 2026-04-17

### Added
- Added `.github/copilot-instructions.md` to define a reusable backlog-autopilot agent procedure for this repository.
- Added Phase 1 indicator catalog and ingestion job definitions for a priority starter set.
- Added Phase 1 normalization and ingestion-run tracking models.
- Added `docs/phase1_macro_data_foundation.md`.
- Added Phase 2 snapshot contract, builder service, in-memory snapshot repository, and comparison metadata baseline.
- Added canonical docs: `docs/snapshot_schema.md`, `docs/state_derivation_rules.md`.

### Changed
- Updated default ingestion indicators to a focused Phase 1 starter set.
- Expanded FRED series mappings for Phase 1 categories and priority indicators.
- Extended in-memory feature store to persist raw payload records, normalized observations, and run metadata.
- Added ingestion throughput metric for raw vs normalized record volumes.
- Expanded Phase 1 storage schema draft to include raw payload, normalized observation, and ingestion run tables.
- Reorganized docs to policy-aligned canonical structure (`architecture`, `roadmap`, `macro_indicator_catalog`, `ingestion_design`, `storage_schema`, `freshness_policy`).
- Simplified README into entry-level quickstart + canonical-doc links.

### Ops
- Added `.github/workflows/copilot-setup-steps.yml` so Copilot cloud agent consistently provisions Python 3.12 + `uv` and installs dependencies before task execution.
