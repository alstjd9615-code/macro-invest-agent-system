# Adding a New Data Provider

This guide walks you through adding a new macro data source (e.g. World Bank,
Bloomberg, ECB) to the `macro-invest-agent-platform`.

---

## Overview

The platform uses a layered provider model:

```
MacroDataSourceContract (abstract)
├── FredMacroDataSource      (priority=10, FRED API)
├── FixtureMacroDataSource   (priority=5,  deterministic fixture)
└── InMemoryMacroDataSource  (priority=1,  mutable test store)

SourceRegistry → selects highest-priority source per indicator
MacroService   → accepts a single MacroDataSourceContract
```

Each provider is an adapter that implements
`MacroDataSourceContract` and optionally provides `SourceMetadata` for
registry-based source selection.

---

## Step-by-Step Guide

### 1. Create the Adapter Package

Create a new directory under `adapters/sources/`:

```
adapters/sources/world_bank/
├── __init__.py
├── world_bank_data_source.py
├── normalizer.py            # indicator-specific value normalisation
└── series_map.py            # mapping from MacroIndicatorType → provider series ID
```

---

### 2. Implement `MacroDataSourceContract`

```python
# adapters/sources/world_bank/world_bank_data_source.py
from core.contracts.macro_data_source import MacroDataSourceContract, SourceMetadata
from core.exceptions.base import ProviderHTTPError, ProviderNetworkError, ProviderTimeoutError
from domain.macro.models import MacroFeature
from core.logging.logger import get_logger

_log = get_logger(__name__)

WORLD_BANK_SERIES_MAP = {
    MacroIndicatorType.GDP: "NY.GDP.MKTP.CD",
    MacroIndicatorType.INFLATION: "FP.CPI.TOTL.ZG",
}


class WorldBankDataSource(MacroDataSourceContract):
    def __init__(self, timeout_s: float = 10.0) -> None:
        self._timeout_s = timeout_s

    @property
    def source_id(self) -> str:
        return "world_bank"

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            source_id="world_bank",
            priority=8,
            supported_indicators=frozenset(
                i.value for i in WORLD_BANK_SERIES_MAP
            ),
        )

    async def fetch_raw(
        self, country: str, indicators: list[str]
    ) -> list[MacroFeature]:
        _log.debug("fetch_started", source="world_bank", country=country)
        features: list[MacroFeature] = []
        for indicator_name in indicators:
            # ... fetch from World Bank API, normalise, append to features
            pass
        return features
```

**Error contract** — raise typed exceptions:

```python
raise ProviderHTTPError("World Bank API HTTP 503", provider_id="world_bank", http_status=503)
raise ProviderTimeoutError("Timed out", provider_id="world_bank", timeout_s=self._timeout_s)
raise ProviderNetworkError("Connection refused", provider_id="world_bank")
```

Never raise bare `RuntimeError` — callers rely on typed exceptions for
`failure_category` routing.

---

### 3. Add a Series Map

```python
# adapters/sources/world_bank/series_map.py
from domain.macro.enums import MacroIndicatorType

WORLD_BANK_SERIES_MAP: dict[MacroIndicatorType, str] = {
    MacroIndicatorType.GDP: "NY.GDP.MKTP.CD",
    MacroIndicatorType.INFLATION: "FP.CPI.TOTL.ZG",
}
```

---

### 4. Add a Normalizer

```python
# adapters/sources/world_bank/normalizer.py
from domain.macro.models import MacroFeature

def normalize_world_bank_observation(...) -> MacroFeature | None:
    # parse raw API response, return MacroFeature
    ...
```

---

### 5. Register in SourceRegistry

```python
from adapters.sources.source_registry import SourceRegistry
from adapters.sources.fred import FredMacroDataSource
from adapters.sources.world_bank.world_bank_data_source import WorldBankDataSource

registry = SourceRegistry([
    FredMacroDataSource(api_key=settings.fred_api_key),
    WorldBankDataSource(),
])

# Select highest-priority source for GDP
source = registry.select("GDP")  # returns FredMacroDataSource (priority=10)
```

---

### 6. Inject into MacroService

```python
from services.macro_service import MacroService

# Use registry-selected source (or pass any source directly)
svc = MacroService(source=registry.select("GDP"))
```

Or pass the registry-selected source directly when constructing the full agent
stack.

---

### 7. Write a Provider Failure Eval

Create a test in `evals/provider_failure/`:

```python
# evals/provider_failure/test_world_bank_failure.py
from core.exceptions.base import ProviderHTTPError

@pytest.mark.asyncio
async def test_world_bank_503_raises_typed_error():
    src = WorldBankDataSource()
    with patch.object(src, "_fetch_observation", side_effect=...):
        with pytest.raises(ProviderHTTPError) as exc_info:
            await src.fetch_raw("US", ["GDP"])
        assert exc_info.value.http_status == 503
        assert exc_info.value.provider_id == "world_bank"
```

---

## Checklist

- [ ] Adapter class in `adapters/sources/<provider>/`
- [ ] `source_id` returns a short, unique, lowercase string
- [ ] `metadata` returns `SourceMetadata` with correct `priority` and `supported_indicators`
- [ ] `fetch_raw` raises `ProviderError` subclasses (not `RuntimeError`)
- [ ] Series map in `series_map.py`
- [ ] Normalizer in `normalizer.py`
- [ ] `__init__.py` exports the main class
- [ ] Unit tests for the normalizer
- [ ] Provider failure eval in `evals/provider_failure/`
- [ ] (Optional) `SourceRegistry.register(new_source)` in the app bootstrap

---

## Source Priority Guidelines

| Priority | Use case                               |
|---|---|
| 10+      | Real-time, authoritative sources (FRED)|
| 8–9      | High-quality secondary sources (World Bank) |
| 5–7      | Fixture / demo sources                 |
| 1–4      | In-memory test stores                  |

Higher priority wins when multiple sources support the same indicator.
