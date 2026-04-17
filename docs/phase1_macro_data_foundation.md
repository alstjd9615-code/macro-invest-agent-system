# Phase 1 — Macro Data Foundation

This document defines the implemented ingestion foundation for a small, high-priority starter set.

## Priority indicators

- CPI (`inflation`) → `CPIAUCSL`
- Unemployment Rate (`unemployment`) → `UNRATE`
- 10Y Yield (`yield_10y`) → `DGS10`
- PMI (`pmi`) → `NAPM`
- Retail Sales (`retail_sales`) → `RSAFS`

Catalog source: `pipelines/ingestion/indicator_catalog.py`

## Source mapping table

FRED series mapping is maintained in:

- `adapters/sources/fred/series_map.py`

## Ingestion jobs

Phase 1 jobs are defined in:

- `pipelines/ingestion/ingestion_jobs.py`

Current split:

- daily rates job (`yield_10y`)
- monthly core job (`inflation`, `unemployment`, `pmi`, `retail_sales`)

## Raw vs normalized storage pattern

For each ingestion snapshot (`snapshot_id`):

- Raw source payload records are stored via `save_raw_records(...)`
- Normalized observations are stored via `save_normalized_records(...)`
- Run metadata is stored via `save_ingestion_run(...)`

Reference adapter:

- `adapters/repositories/in_memory_feature_store.py`

## Normalized schema requirements

Normalized observation model (`NormalizedMacroObservation`) includes:

- `indicator_id`
- `observation_date`
- `release_date`
- `fetched_at`
- `value`
- `unit`
- `frequency`
- `source`
- `source_series_id`
- `region`
- revision metadata (`revision_status`, `revision_number`)
- freshness metadata (`freshness.status`, lag fields)

## Freshness policy (Phase 1 baseline)

Freshness states:

- `fresh`
- `late`
- `stale`
- `unknown`

Baseline behavior:

- compare `fetched_at - observation_date` against an indicator lag threshold
- mark `late` over threshold
- mark `stale` over 2x threshold

## Revision policy (Phase 1 baseline)

Phase 1 stores sufficient metadata for revision tracking:

- raw source payload retention per snapshot
- normalized revision fields (`revision_status`, `revision_number`)

Current policy values:

- `initial`
- `revised`
- `final`
- `unknown`
