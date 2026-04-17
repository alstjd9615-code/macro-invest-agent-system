# Storage Schema

## Layered storage model (Phase 1)

1. **Raw layer**  
   Preserve provider payload metadata for audit/revision detection.
2. **Normalized layer**  
   Store standardized observations for downstream use.
3. **Run layer**  
   Store ingestion execution metadata and counts.

## Canonical model references

- `RawFeatureRecord` — `pipelines/ingestion/models.py`
- `NormalizedMacroObservation` — `pipelines/ingestion/models.py`
- `IngestionRunRecord` — `pipelines/ingestion/models.py`

## Schema draft

Migration draft and table intent:

- `alembic/versions/0001_feature_store_initial.py`

This draft documents:

- `feature_snapshots`
- `raw_observation_payloads`
- `normalized_observations`
- `ingestion_runs`
