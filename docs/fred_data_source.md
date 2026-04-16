# FRED Macro Data Source

The FRED adapter fetches live macroeconomic indicator data from the
[Federal Reserve Economic Data](https://fred.stlouisfed.org/) (FRED) API
published by the St. Louis Fed.

---

## Overview

`FredMacroDataSource` implements the
[`MacroDataSourceContract`](../core/contracts/macro_data_source.py) and can be
dropped into any code that depends on that contract, including
`MacroIngestionService`.

```
MacroIngestionService
  └── FredMacroDataSource          ← fetches live FRED observations
        ├── series_map.py           ← maps MacroIndicatorType → FRED series ID
        ├── normalizer.py           ← converts raw string value → MacroFeature
        └── _fetch_latest_observation() ← urllib.request HTTP call
```

---

## Configuration

All settings are loaded from `core/config/settings.py` (via environment
variables or `.env`):

| Setting | Default | Description |
|---|---|---|
| `FRED_API_KEY` | `None` | FRED API key — **required** for live calls |
| `FRED_BASE_URL` | `https://api.stlouisfed.org/fred` | FRED REST API base URL |
| `FRED_REQUEST_TIMEOUT_S` | `10.0` | HTTP request timeout in seconds |

Obtain a free API key at <https://fred.stlouisfed.org/docs/api/api_key.html>.

```dotenv
# .env (local development)
FRED_API_KEY=your_fred_api_key_here
```

---

## Supported Series

The adapter covers the five indicators in `DEFAULT_INDICATORS`:

| `MacroIndicatorType` | FRED Series ID | Description |
|---|---|---|
| `gdp` | `GDPC1` | Real Gross Domestic Product (Billions of Chained 2017 Dollars, Seasonally Adjusted Annual Rate) |
| `inflation` | `CPIAUCSL` | Consumer Price Index for All Urban Consumers: All Items in U.S. City Average (Index 1982-84=100) |
| `unemployment` | `UNRATE` | Unemployment Rate (Seasonally Adjusted, %) |
| `interest_rate` | `FEDFUNDS` | Federal Funds Effective Rate (%) |
| `bond_yield` | `DGS10` | Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity (%) |

Indicators **not** in this map are silently skipped — no `MacroFeature` is
returned for them.

---

## Usage

### Standalone

```python
from core.config.settings import get_settings
from adapters.sources.fred import FredMacroDataSource

settings = get_settings()
source = FredMacroDataSource(
    api_key=settings.fred_api_key.get_secret_value(),
    base_url=settings.fred_base_url,
    timeout_s=settings.fred_request_timeout_s,
)
features = await source.fetch_raw("US", ["gdp", "inflation", "unemployment"])
for f in features:
    print(f.indicator_type, f.value, f.timestamp.date())
```

### With MacroIngestionService

```python
from core.config.settings import get_settings
from adapters.sources.fred import FredMacroDataSource
from adapters.repositories.in_memory_feature_store import InMemoryFeatureStore
from pipelines.ingestion.macro_ingestion_service import MacroIngestionService

settings = get_settings()
source = FredMacroDataSource(
    api_key=settings.fred_api_key.get_secret_value(),
)
service = MacroIngestionService(
    source=source,
    repository=InMemoryFeatureStore(),
)
snapshot = await service.ingest("US")
print(f"Ingested {snapshot.features_count} features from FRED")
```

---

## Error Handling

| Condition | Raised exception | Message pattern |
|---|---|---|
| `api_key` is `None` or empty | `RuntimeError` | `"requires a non-empty api_key"` |
| HTTP error (4xx / 5xx) | `RuntimeError` | `"FRED API HTTP error <code>"` |
| Network timeout | `RuntimeError` | `"FRED API request timed out after <n>s"` |
| Network / OS error | `RuntimeError` | `"FRED API network error"` |

`MacroIngestionService` propagates `RuntimeError` from the source unchanged,
so callers always receive an actionable message.

---

## Design Notes

* **No new dependencies** — the adapter uses `urllib.request` (stdlib) only.
* **Read-only** — the adapter never modifies FRED or any local state.
* **Deterministic per observation** — given the same latest FRED observation,
  `normalize_fred_observation()` always returns the same `MacroFeature`.
* **Partial data** — if FRED returns only 3 of 5 requested indicators (e.g.
  because some series have no recent observation), `features_count` reflects
  the actual number of features returned.
* **FRED sentinel value** — FRED uses `"."` to indicate a missing /
  not-yet-released value.  The normalizer returns `None` for this sentinel
  and the feature is omitted from the result list.

---

## Testing

The test suite exercises the adapter without making real HTTP calls:

```bash
# Run all FRED-related tests
pytest tests/unit/pipelines/test_fred_normalizer.py tests/unit/pipelines/test_fred_source.py -v
```

Test files:

| File | Covers |
|---|---|
| `tests/unit/pipelines/test_fred_normalizer.py` | `normalize_fred_observation()` — valid values, missing sentinel, non-numeric, out-of-range |
| `tests/unit/pipelines/test_fred_source.py` | Series-map coverage, constructor guard, mocked `fetch_raw`, ingestion integration, HTTP error, timeout error |
