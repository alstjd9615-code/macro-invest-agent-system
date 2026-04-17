# Storage Schema

## Layered storage model (Phase 1)

1. **Raw layer**  
   Preserve provider payload metadata for audit/revision detection.
2. **Normalized layer**  
   Store standardized observations for downstream use.
3. **Run layer**  
   Store ingestion execution metadata and counts.

## Regime layer model (Phase 3)

4. **Regime layer**  
   Store built macro regimes keyed by as-of date, with transition metadata.

## Canonical model references

- `RawFeatureRecord` — `pipelines/ingestion/models.py`
- `NormalizedMacroObservation` — `pipelines/ingestion/models.py`
- `IngestionRunRecord` — `pipelines/ingestion/models.py`
- `MacroRegime` — `domain/macro/regime.py`

## Schema draft

Migration draft and table intent:

- `alembic/versions/0001_feature_store_initial.py`

This draft documents:

- `feature_snapshots`
- `raw_observation_payloads`
- `normalized_observations`
- `ingestion_runs`
- `macro_regimes` (planned durable table; in-memory adapter currently active)
