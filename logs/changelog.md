# Changelog

## 2026-04-17

### Added
- Added `.github/copilot-instructions.md` to define a reusable backlog-autopilot agent procedure for this repository.
- Added Phase 1 indicator catalog and ingestion job definitions for a priority starter set.
- Added Phase 1 normalization and ingestion-run tracking models.
- Added `docs/phase1_macro_data_foundation.md`.

### Changed
- Updated default ingestion indicators to a focused Phase 1 starter set.
- Expanded FRED series mappings for Phase 1 categories and priority indicators.
- Extended in-memory feature store to persist raw payload records, normalized observations, and run metadata.

### Ops
- Added `.github/workflows/copilot-setup-steps.yml` so Copilot cloud agent consistently provisions Python 3.12 + `uv` and installs dependencies before task execution.
