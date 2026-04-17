# Regime Builder

Canonical source: `services/macro_regime_service.py`

The Phase 3 regime builder creates a `MacroRegime` for a selected `as_of_date`
from the latest available snapshot on or before that date.

## Build flow

1. Load latest snapshot on or before target date.
2. Map snapshot states to regime label/family.
3. Derive confidence from freshness/degraded/state coherence.
4. Forward `missing_indicators` as `missing_inputs`.
5. Build deterministic rationale summary and supporting states.

## Notes

- Builder raises `ValueError` when no baseline snapshot exists.
- Persistence and transition tracking are handled in subsequent Phase 3 tasks.
