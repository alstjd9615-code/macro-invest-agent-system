# Failure Taxonomy

This document describes all failure categories used in the
`macro-invest-agent-platform`, when they are raised, and what callers should do
when they encounter each one.

---

## Failure Category Enum

All categories are defined in `core/exceptions/failure_category.py` as a
`StrEnum`:

```python
from core.exceptions.failure_category import FailureCategory

# Values
FailureCategory.PROVIDER_TIMEOUT  # "PROVIDER_TIMEOUT"
FailureCategory.PROVIDER_HTTP     # "PROVIDER_HTTP"
FailureCategory.PROVIDER_NETWORK  # "PROVIDER_NETWORK"
FailureCategory.STALE_DATA        # "STALE_DATA"
FailureCategory.PARTIAL_DATA      # "PARTIAL_DATA"
FailureCategory.SCHEMA_ERROR      # "SCHEMA_ERROR"
FailureCategory.UNKNOWN           # "UNKNOWN"
```

---

## Exception Hierarchy

```
AppError
├── ProviderError                    → all external-provider failures
│   ├── ProviderTimeoutError         → request timed out
│   ├── ProviderHTTPError            → non-2xx HTTP response
│   └── ProviderNetworkError         → OS-level / network I/O failure
├── StaleDataError                   → data older than freshness threshold
├── PartialDataError                 → fewer indicators than requested
├── SchemaConformanceError           → unexpected response structure
├── ValidationError                  → input validation failure
├── NotFoundError                    → resource not found
├── DomainError                      → business-rule violation
└── MCPToolError                     → MCP tool execution failure
```

---

## Categories in Detail

### `PROVIDER_TIMEOUT`

**Exception**: `ProviderTimeoutError`  
**When raised**: The HTTP request to an external provider (e.g. FRED API) did
not complete within the configured timeout.  
**Callers should**: Log the failure. Do not retry automatically (retry logic is
deferred). Surface `success=False, failure_category="PROVIDER_TIMEOUT"` to the
consumer. The `timeout_s` attribute carries the configured limit.

```python
raise ProviderTimeoutError(
    "FRED request timed out",
    provider_id="fred",
    timeout_s=30.0,
)
```

---

### `PROVIDER_HTTP`

**Exception**: `ProviderHTTPError`  
**When raised**: The provider returned a non-success HTTP status code (e.g.
503, 429, 401).  
**Callers should**: Inspect `exc.http_status`. 4xx statuses (401, 403) indicate
misconfiguration; 5xx statuses indicate provider outage. Surface
`failure_category="PROVIDER_HTTP"`.

```python
raise ProviderHTTPError(
    f"FRED returned HTTP 503",
    provider_id="fred",
    http_status=503,
)
```

---

### `PROVIDER_NETWORK`

**Exception**: `ProviderNetworkError`  
**When raised**: An OS-level error prevented the HTTP request from completing
(e.g. DNS resolution failure, connection refused).  
**Callers should**: Surface `failure_category="PROVIDER_NETWORK"`. Check
network access / DNS configuration.

---

### `STALE_DATA`

**Exception**: `StaleDataError`  
**When raised**: Data returned by the adapter is older than the expected
freshness window.  The FRED adapter does not currently emit this (data age
tracking is deferred); future adapters that track freshness should raise it.  
**Callers should**: Surface `is_degraded=True, failure_category="STALE_DATA"`.
Consumers should not treat stale data as current. The `stale_since` attribute
carries the timestamp at which the data became stale (may be `None`).

---

### `PARTIAL_DATA`

**Exception**: `PartialDataError`  
**When raised**: Fewer indicators were returned than were requested. This is a
*degraded* state — the partial result is schema-valid but incomplete.  
**Callers should**: Surface `is_degraded=True, failure_category="PARTIAL_DATA"`.
`success` may remain `True` for partial-but-usable results. The
`available_count` and `requested_count` attributes carry the counts.

---

### `SCHEMA_ERROR`

**Exception**: `SchemaConformanceError`  
**When raised**: An external API response did not match the expected schema.  
**Callers should**: Surface `failure_category="SCHEMA_ERROR"`. File a bug
against the provider integration. Do not retry.

---

### `UNKNOWN`

**No specific exception** — catch-all for unexpected errors.  
**When raised**: An unexpected exception fell through all typed exception
handlers.  
**Callers should**: Surface `failure_category="UNKNOWN"`. Inspect the
`error_message` and application logs for details.

---

## Response Fields

All MCP responses (`GetMacroSnapshotResponse`, `GetMacroFeaturesResponse`,
`RunSignalEngineResponse`) and agent responses (`AgentResponse` and subclasses)
carry:

| Field              | Type                       | Meaning                                       |
|---|---|---|
| `success`          | `bool`                     | `True` for clean success; `False` for failures |
| `error_message`    | `str \| None`              | Human-readable description when `success=False` |
| `failure_category` | `FailureCategory \| None`  | Machine-readable category; `None` on clean success |
| `is_degraded`      | `bool`                     | `True` when partial/stale but schema-valid     |

### Rules

- `failure_category` is always set when `success=False`.
- `is_degraded=True` is set for `STALE_DATA` and `PARTIAL_DATA` paths, even
  when `success` remains `True` (partial data that is still usable).
- `is_degraded=False` and `failure_category=None` together indicate a clean,
  fresh, complete response.

---

## What Callers Should Do

```python
response = await adapter.get_macro_snapshot(request_id="r", country="US")

if not response.success:
    if response.failure_category == FailureCategory.PROVIDER_TIMEOUT:
        # Surface timeout to end-user; suggest retrying later
        ...
    elif response.failure_category == FailureCategory.PROVIDER_HTTP:
        # Check provider status page
        ...
    else:
        # Log and surface generic error
        ...
elif response.is_degraded:
    # Data is partial or stale — display with warning
    ...
else:
    # Clean success — proceed normally
    ...
```
