# Observability and Tracing

This document describes the structured logging and tracing conventions used across
the `macro-invest-agent-platform`. After PR1 (Phase 4), every request is traceable
end-to-end across all architectural layers.

---

## How to Trace a Request

Every request flowing through `AgentRuntime.invoke` (or `LangChainAgentRuntime.invoke`)
gets a unique `trace_id` bound to the async execution context:

```python
from agent.runtime.agent_runtime import AgentRuntime
from agent.schemas import SignalReviewRequest

runtime = AgentRuntime(service)
result = await runtime.invoke(
    SignalReviewRequest(request_id="req-001", signal_ids=["bull_market"])
)
```

The runtime automatically calls `bind_request_context(request_id, trace_id, session_id)`,
which sets two ContextVars and binds them into structlog's context so that every
subsequent log record in the same async task carries these fields.

### Fields bound automatically

| Field        | Source                         | Present when         |
|---|---|---|
| `trace_id`   | `set_trace_id()` (auto UUID)   | Always               |
| `request_id` | `request.request_id`           | Always               |
| `session_id` | `request.session_id`           | Non-empty session only |

---

## Log Events by Layer

### `runtime` layer (`agent/runtime/agent_runtime.py`)

| Event               | Level | Fields                                      |
|---|---|---|
| `request_started`   | INFO  | `request_type`                              |
| `request_completed` | INFO  | `request_type`, `success`                   |
| `dispatching_operation` | DEBUG | `operation`                             |
| `operation_complete`| DEBUG | `layer="runtime"`, `operation`, `latency_ms`|
| `operation_failed`  | WARN  | `layer="runtime"`, `operation`, `latency_ms`, `error` |

### `service` layer (`agent/service.py`)

| Event               | Level | Fields                                      |
|---|---|---|
| `service_called`    | INFO  | `operation`, `country`                      |
| `service_done`      | INFO  | `operation`, `success`                      |
| `service_failed`    | WARN  | `operation`, `tool` or `error`              |
| `service_prior_missing` | WARN | `operation`, `prior_label`              |
| `operation_complete`| DEBUG | `layer="service"`, `operation`, `latency_ms`|
| `operation_failed`  | WARN  | `layer="service"`, `operation`, `latency_ms`, `error` |

### `mcp_adapter` layer (`agent/mcp_adapter.py`)

| Event               | Level | Fields                                      |
|---|---|---|
| `tool_called`       | DEBUG | `tool`, `country`                           |
| `tool_done`         | DEBUG | `tool`, `success`                           |
| `tool_failed`       | WARN  | `tool`, `error`                             |
| `operation_complete`| DEBUG | `layer="mcp_adapter"`, `operation`, `latency_ms` |
| `operation_failed`  | WARN  | `layer="mcp_adapter"`, `operation`, `latency_ms`, `error` |

### `mcp_tool` layer (`mcp/tools/`)

| Event                 | Level | Fields                                      |
|---|---|---|
| `mcp_tool_invoked`    | DEBUG | `tool`, `request_id`                        |
| `mcp_tool_returned`   | DEBUG | `tool`, `success`, and tool-specific fields |
| `operation_complete`  | DEBUG | `layer="mcp_tool"`, `operation`, `latency_ms` |
| `operation_failed`    | WARN  | `layer="mcp_tool"`, `operation`, `latency_ms`, `error` |

### `service` layer — services (`services/macro_service.py`, `services/signal_service.py`)

| Event                   | Level | Fields                                    |
|---|---|---|
| `service_fetch_started` | DEBUG | `operation`, `country`, `indicator_count` |
| `service_fetch_complete`| DEBUG | `operation`, `country`, `features_returned` or `features_count` |

### FRED adapter (`adapters/sources/fred/fred_macro_data_source.py`)

| Event               | Level | Fields                                |
|---|---|---|
| `fred_fetch_started`| DEBUG | `series_id`, `country`                |
| `fred_fetch_complete`| DEBUG | `series_id`, `country`, `latency_ms`, `result` |
| `fred_fetch_failed` | WARN  | `series_id`, `error`, optional `http_status` or `timeout_s` |

> **Security note**: The FRED API key is **never** logged. Only `series_id` and
> request metadata are included.

### Ingestion pipeline (`pipelines/ingestion/macro_ingestion_service.py`)

| Event               | Level | Fields                                       |
|---|---|---|
| `ingestion_started` | INFO  | `country`, `source`, `indicator_count`       |
| `ingestion_complete`| INFO  | `country`, `features_count`, `snapshot_id`   |

---

## Enabling JSON vs Pretty Mode

Control the output format via environment variables:

```bash
# Human-readable coloured output (local dev)
LOG_PRETTY=true APP_ENV=local python ...

# JSON output (production / log aggregators)
LOG_PRETTY=false LOG_LEVEL=INFO python ...
```

See `core/config/settings.py` for all settings.

---

## Latency Breakdown

`timed_operation(layer, operation, log)` is used at each layer boundary.
In JSON mode, aggregate latency per layer by grouping on `layer` field:

```bash
# Example: jq to extract per-layer latency from JSON logs
cat app.log | jq 'select(.event=="operation_complete") | {layer, operation, latency_ms}'
```

---

## Adding New Instrumentation

1. Import `get_logger` from `core.logging.logger` (not stdlib `logging`).
2. Use `timed_operation("your_layer", "your_op", log)` around I/O or expensive
   calls.
3. Use keyword arguments for all structured fields (e.g. `log.info("event", key=value)`).
4. Never log secrets, API keys, PII, or raw exception tracebacks as structured
   fields — use `log.exception()` only for unexpected errors.
