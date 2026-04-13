# MCP Entrypoints

This document describes the callable MCP tool boundary — the thin layer that
wires the deterministic macro-to-signal flow into agent-consumable tool calls.

---

## Overview

MCP tools are **read-only, async handler functions** that:

1. Accept a validated request schema as input.
2. Delegate work to the service layer (no business logic in the tool itself).
3. Return a structured response schema, always including `success` and
   `request_id` fields.
4. **Never raise exceptions** — all errors are captured and returned as
   `success=False` with an `error_message`.

```
Agent / caller
     │
     │  MCPRequest (validated Pydantic model)
     ▼
┌────────────────────────┐
│     MCP Tool Handler   │  ← thin; no business logic
└────────┬───────────────┘
         │
         ▼
   Service Layer  ──►  Domain Layer  ──►  SignalEngine
         │
         ▼
┌────────────────────────┐
│     MCPResponse        │  ← structured; always success or error
└────────────────────────┘
```

---

## Available Tools

### `handle_get_macro_features`

**Module**: `mcp.tools.get_macro_features`

Fetches specific macro indicators for a given country.

| | |
|---|---|
| **Request schema** | `GetMacroFeaturesRequest` |
| **Response schema** | `GetMacroFeaturesResponse` |
| **Service called** | `MacroServiceInterface.fetch_features` |

**Request fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `request_id` | `str` | ✅ | — | Unique request identifier |
| `timestamp` | `datetime` | — | `utcnow()` | Request creation time |
| `indicator_types` | `list[str]` | ✅ | — | Macro indicator enum values to fetch (e.g. `["gdp", "inflation"]`) |
| `country` | `str` | — | `"US"` | ISO 3166-1 alpha-2 country code |

**Response fields** (in addition to base `MCPResponse`)

| Field | Type | Description |
|---|---|---|
| `features_count` | `int` | Number of macro features returned |

**Error conditions**

| Condition | `error_message` content |
|---|---|
| `indicator_types` is empty | `"indicator_types must not be empty."` |
| Service raises `ValueError` | The exception message |
| Any other exception | `"Failed to fetch features: <exc>"` |

---

### `handle_get_macro_snapshot`

**Module**: `mcp.tools.get_macro_features`

Retrieves a complete macro snapshot (all available indicators) for a given country.

| | |
|---|---|
| **Request schema** | `GetMacroSnapshotRequest` |
| **Response schema** | `GetMacroSnapshotResponse` |
| **Service called** | `MacroServiceInterface.get_snapshot` |

**Request fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `request_id` | `str` | ✅ | — | Unique request identifier |
| `timestamp` | `datetime` | — | `utcnow()` | Request creation time |
| `country` | `str` | — | `"US"` | ISO 3166-1 alpha-2 country code |

**Response fields** (in addition to base `MCPResponse`)

| Field | Type | Description |
|---|---|---|
| `snapshot_timestamp` | `datetime` | Reference time of the macro snapshot |
| `features_count` | `int` | Number of features in the snapshot |

**Error conditions**

| Condition | `error_message` content |
|---|---|
| Any exception from service | `"Failed to fetch snapshot: <exc>"` |

---

### `handle_run_signal_engine`

**Module**: `mcp.tools.run_signal_engine`

Resolves signal IDs to definitions, fetches a macro snapshot, and runs the
deterministic signal evaluation engine.

| | |
|---|---|
| **Request schema** | `RunSignalEngineRequest` |
| **Response schema** | `RunSignalEngineResponse` |
| **Services called** | `MacroServiceInterface.get_snapshot`, `SignalServiceInterface.run_engine` |
| **Registry used** | `domain.signals.registry.SignalRegistry` |

**Request fields**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `request_id` | `str` | ✅ | — | Unique request identifier |
| `timestamp` | `datetime` | — | `utcnow()` | Request creation time |
| `signal_ids` | `list[str]` | ✅ | — | IDs of signal definitions to evaluate |
| `country` | `str` | — | `"US"` | Country code for macro data |
| `use_latest_snapshot` | `bool` | — | `True` | Always fetch a fresh snapshot (reserved for future snapshot injection) |

**Response fields** (in addition to base `MCPResponse`)

| Field | Type | Description |
|---|---|---|
| `engine_run_id` | `str` | UUID identifying this engine run |
| `signals_generated` | `int` | Total signals produced |
| `buy_signals` | `int` | Count of `BUY` signals |
| `sell_signals` | `int` | Count of `SELL` signals |
| `hold_signals` | `int` | Count of `HOLD` signals |
| `execution_time_ms` | `float` | Wall-clock time for engine execution (ms) |

**Error conditions**

| Condition | `error_message` content |
|---|---|
| `signal_ids` is empty | `"signal_ids must not be empty."` |
| One or more unknown IDs | `"Unknown signal ID(s): '<id>'."` |
| Macro snapshot fetch fails | `"Failed to fetch macro snapshot: <exc>"` |
| Signal engine raises | `"Signal engine execution failed: <exc>"` |

---

## Signal Registry

Built-in signal definitions are available via `domain.signals.registry.default_registry`:

| Signal ID | Type | Description |
|---|---|---|
| `bull_market` | `BUY` | Positive GDP growth + contained inflation |
| `recession_warning` | `SELL` | Elevated unemployment + contracting GDP |
| `hold_neutral` | `HOLD` | PMI in the 45–55 borderline range |

Custom definitions can be injected via the `registry` parameter of
`handle_run_signal_engine` (useful in tests or agent orchestration).

---

## Base Response Schema

All MCP responses include these fields from `MCPResponse`:

| Field | Type | Description |
|---|---|---|
| `request_id` | `str` | Echoes the `request_id` from the request |
| `timestamp` | `datetime` | Response creation time |
| `success` | `bool` | `True` on success, `False` on any error |
| `error_message` | `str \| None` | Human-readable error if `success=False` |

---

## Read-Only Boundary

The MCP tool layer is **strictly read-only**:

- Tools **query** macro data and evaluate signals.
- Tools do **not** write to any store, trigger side effects, or mutate domain state.
- Tools do **not** contain business logic — all decisions live in the domain and service layers.
- Tools do **not** expose FastAPI routes or HTTP endpoints.

This constraint keeps the boundary simple, auditable, and safe for agent consumption.

---

## Example Usage (Python)

```python
import asyncio
from mcp.tools import handle_run_signal_engine
from mcp.schemas.run_signal_engine import RunSignalEngineRequest
from services.macro_service import MacroService
from services.signal_service import SignalService

async def main() -> None:
    request = RunSignalEngineRequest(
        request_id="req-001",
        signal_ids=["bull_market", "recession_warning"],
        country="US",
    )
    response = await handle_run_signal_engine(
        request=request,
        macro_service=MacroService(),
        signal_service=SignalService(),
    )
    if response.success:
        print(f"Run {response.engine_run_id}: {response.signals_generated} signal(s)")
        print(f"  BUY={response.buy_signals}  SELL={response.sell_signals}  HOLD={response.hold_signals}")
    else:
        print(f"Error: {response.error_message}")

asyncio.run(main())
```
