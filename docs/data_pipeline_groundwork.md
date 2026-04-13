# Data Pipeline Groundwork

This document describes the minimum data pipeline groundwork introduced to
give the system clear data-source and feature-store boundaries, without
integrating real external providers yet.

---

## Overview

The pipeline layer follows a clean three-tier structure:

```
┌───────────────────────────────────────────────────────────────┐
│                      Contracts (interfaces)                   │
│  core/contracts/macro_data_source.py                          │
│  core/contracts/feature_store_repository.py                   │
└──────────────────────────┬────────────────────────────────────┘
                           │  implemented by
┌──────────────────────────▼────────────────────────────────────┐
│                      Adapters                                  │
│  adapters/sources/fixture_macro_data_source.py                │
│  adapters/sources/in_memory_macro_data_source.py              │
│  adapters/repositories/in_memory_feature_store.py             │
└──────────────────────────┬────────────────────────────────────┘
                           │  used by
┌──────────────────────────▼────────────────────────────────────┐
│                      Ingestion service                         │
│  pipelines/ingestion/macro_ingestion_service.py               │
│  pipelines/ingestion/models.py                                 │
└───────────────────────────────────────────────────────────────┘
```

---

## Contracts

Contracts are abstract base classes (ABCs) defined in `core/contracts/`.
They specify the minimum interface any adapter must implement.

### `core/contracts/macro_data_source.py` — `MacroDataSourceContract`

| Member | Description |
|---|---|
| `source_id: str` (property) | Short identifier for the data source (e.g. `"fixture"`, `"fred"`) |
| `fetch_raw(country, indicators) → list[MacroFeature]` | Fetch raw macro features for a country and set of indicators |

### `core/contracts/feature_store_repository.py` — `FeatureStoreRepositoryContract`

| Member | Description |
|---|---|
| `save_snapshot(snapshot)` | Persist a `FeatureSnapshot` |
| `get_latest_snapshot(country) → FeatureSnapshot \| None` | Retrieve the most recent snapshot for a country |
| `list_snapshots(country, limit) → list[FeatureSnapshot]` | List the `limit` most recent snapshots for a country (newest-first) |

---

## Models

### `pipelines/ingestion/models.py` — `FeatureSnapshot`

The unit of data produced and persisted by the ingestion service.

| Field | Type | Description |
|---|---|---|
| `snapshot_id` | `str` | UUID4 auto-generated unique ID |
| `country` | `str` | ISO 3166-1 alpha-2 country code |
| `source_id` | `str` | Identifier of the data source that provided the features |
| `ingested_at` | `datetime` | UTC timestamp of ingestion |
| `features` | `list[MacroFeature]` | Non-empty list of macro features |
| `features_count` | `int` | Derived from `len(features)` — always kept in sync |

`FeatureSnapshot` is a Pydantic model with `extra="allow"` behaviour (default)
and a `model_post_init` hook that keeps `features_count` in sync.

---

## Adapters

### Data source adapters (`adapters/sources/`)

#### `FixtureMacroDataSource`

Returns hard-coded, fully deterministic feature values for all
`MacroIndicatorType` members.  The reference timestamp is fixed to
`2026-01-01T00:00:00Z` so tests always produce the same output.

| Property / Method | Behaviour |
|---|---|
| `source_id` | `"fixture"` |
| `fetch_raw(country, indicators)` | Returns fixture values; unknown indicators are silently skipped |
| `country_override` constructor arg | Forces all features to use the given country code |

#### `InMemoryMacroDataSource`

Mutable in-memory store keyed by `(country, indicator)`.  Tests can call
`set_feature(country, indicator, feature)` to inject precise values.

| Property / Method | Behaviour |
|---|---|
| `source_id` | `"in_memory"` |
| `fetch_raw(country, indicators)` | Returns only stored features; unknown or unstored indicators are omitted |
| `set_feature(country, indicator, feature)` | Store a feature |
| `clear()` | Remove all stored features |

---

### Repository adapters (`adapters/repositories/`)

#### `InMemoryFeatureStore`

Stores `FeatureSnapshot` objects in a Python list.  Useful in tests and as the
default development repository when no database is configured.

| Method | Behaviour |
|---|---|
| `save_snapshot(snapshot)` | Append snapshot; raises `TypeError` for wrong type |
| `get_latest_snapshot(country)` | Return most recently appended snapshot for country; `None` if empty |
| `list_snapshots(country, limit)` | Return `limit` most recent snapshots for country, newest-first |
| `all_snapshots()` | Return all snapshots in insertion order (test introspection) |

---

## Ingestion Service

### `pipelines/ingestion/macro_ingestion_service.py` — `MacroIngestionService`

Orchestrates: **fetch → snapshot → persist → return**.

```
service = MacroIngestionService(source=FixtureMacroDataSource(), repository=InMemoryFeatureStore())
snapshot = await service.ingest(country="US")
```

| Method | Description |
|---|---|
| `ingest(country, indicators)` | Fetch, package, and persist a `FeatureSnapshot`; returns the snapshot |

`DEFAULT_INDICATORS` is the list of indicator names fetched when the caller
does not specify any:

```python
["gdp", "inflation", "unemployment", "interest_rate", "bond_yield"]
```

**Raises `RuntimeError`** if the data source returns no features so callers
can detect and handle empty-data scenarios explicitly.

---

## Database Schema (Draft)

`alembic/versions/0001_feature_store_initial.py` contains a draft Alembic
migration that describes the intended `feature_snapshots` table:

| Column | Type | Notes |
|---|---|---|
| `snapshot_id` | `TEXT PRIMARY KEY` | UUID4 string |
| `country` | `TEXT NOT NULL` | ISO 3166-1 alpha-2 |
| `source_id` | `TEXT NOT NULL` | Data source identifier |
| `ingested_at` | `TIMESTAMPTZ NOT NULL` | UTC ingestion timestamp |
| `features_count` | `INTEGER NOT NULL >= 0` | Derived feature count |
| `features_json` | `JSONB NOT NULL` | Serialised `MacroFeature` list |

The migration is a stub (no-op `upgrade`/`downgrade`) until a database
connection is configured.  Activate by:

1. Setting `DATABASE_URL` in the environment.
2. Implementing the `op.create_table` / `op.drop_table` calls in the migration
   file.
3. Running `alembic upgrade head`.

---

## Usage Example

```python
import asyncio
from adapters.sources.fixture_macro_data_source import FixtureMacroDataSource
from adapters.repositories.in_memory_feature_store import InMemoryFeatureStore
from pipelines.ingestion.macro_ingestion_service import MacroIngestionService

async def main() -> None:
    service = MacroIngestionService(
        source=FixtureMacroDataSource(),
        repository=InMemoryFeatureStore(),
    )
    snapshot = await service.ingest(country="US")
    print(f"Ingested {snapshot.features_count} features (snapshot_id={snapshot.snapshot_id})")

asyncio.run(main())
```

---

## Extension Path

### Connecting a real data provider

1. Implement `MacroDataSourceContract` in a new file under `adapters/sources/`
   (e.g. `fred_macro_data_source.py`).
2. Wire the new source into `MacroIngestionService` at construction.
3. No changes needed to the contracts, models, or tests.

### Connecting a real database

1. Implement `FeatureStoreRepositoryContract` in `adapters/repositories/`
   backed by SQLAlchemy (the dependency is already in `pyproject.toml`).
2. Activate the Alembic migration in `alembic/versions/0001_feature_store_initial.py`.
3. Swap `InMemoryFeatureStore` for the SQLAlchemy repository at construction.

### Adding new indicator types

1. Add the new value to `domain.macro.enums.MacroIndicatorType`.
2. Add a fixture value to `_FIXTURE_VALUES` in `FixtureMacroDataSource`.
3. Optionally extend `DEFAULT_INDICATORS` in `MacroIngestionService`.

---

## Out of Scope (This Version)

- 🚫 Real external provider integration (FRED, World Bank, etc.)
- 🚫 Live database connection (Alembic migration is a stub)
- 🚫 Streaming or scheduled ingestion
- 🚫 Feature computation / transformation beyond packaging raw values
- 🚫 Agent-layer integration (the agent layer remains independent)
