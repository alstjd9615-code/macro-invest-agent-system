# Ingestion Design

Canonical ingestion entrypoint: `pipelines/ingestion/macro_ingestion_service.py`

## Flow

1. Select indicators (default: Phase 1 priority set).
2. Fetch source observations via `MacroDataSourceContract`.
3. Create `FeatureSnapshot`.
4. Persist layered outputs:
   - raw payload records
   - normalized observations
   - ingestion run record
5. Emit ingestion metrics.

## Jobs

Defined in `pipelines/ingestion/ingestion_jobs.py`:

- `macro-daily-rates` (daily): `yield_10y`
- `macro-monthly-core` (monthly): `inflation`, `unemployment`, `pmi`, `retail_sales`

## Contracts

- Source contract: `core/contracts/macro_data_source.py`
- Repository contract: `core/contracts/feature_store_repository.py`
