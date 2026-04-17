# Freshness Policy

Canonical implementation: `pipelines/ingestion/models.py` (`FreshnessStatus`, `build_normalized_observation`).

## States

- `fresh`
- `late`
- `stale`
- `unknown`

## Baseline logic (Phase 1)

- Compute lag as: `fetched_at - observation_date`.
- Compare to per-indicator threshold (`expected_max_lag_hours`).
- `late`: lag > threshold.
- `stale`: lag > 2x threshold.
- `fresh`: otherwise.
- `unknown`: reserved for cases where lag/frequency context is unavailable.

## Required timestamp separation

- `observation_date`: when the value was observed.
- `release_date`: when the source released the observation.
- `fetched_at`: when ingestion retrieved the payload.
