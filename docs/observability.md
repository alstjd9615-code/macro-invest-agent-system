# Observability and Tracing

This document describes the structured logging, correlation ID propagation, and
OpenTelemetry distributed tracing conventions used across the
`macro-invest-agent-platform`.  After Phase 5 PR1, every user request and
every ingestion pipeline run can be traced end-to-end across all architectural
layers.

---

## Architecture: two complementary layers

| Layer | What it provides | Where to look |
|---|---|---|
| **Structured logs** (structlog) | Human-readable / JSON records with correlation IDs, event names, latency, and failure details | log aggregator (stdout / JSON) |
| **OTel distributed traces** | Nested spans with timing, attributes, and parent–child relationships across service boundaries | Jaeger / Grafana Tempo / any OTLP backend |

Logs and traces are correlated via two mechanisms:
1. `trace_id` / `request_id` appear in both log records and as span attributes.
2. When an OTel span is active, log records also carry `otel_trace_id` and
   `otel_span_id` so that logs can be looked up from a trace view.

---

## OpenTelemetry tracing

### Enabling tracing

Tracing is **disabled by default**.  Set the following environment variables
to enable it:

```bash
TRACING_ENABLED=true
OTLP_ENDPOINT=http://localhost:4318    # Jaeger / Tempo OTLP-HTTP endpoint
OTEL_SERVICE_NAME=macro-invest-agent-platform
OTEL_SAMPLE_RATE=1.0                   # 1.0 = 100%; reduce in high-volume staging
```

Call `configure_tracing()` once at application startup:

```python
from core.tracing import configure_tracing
configure_tracing()   # reads Settings automatically
```

When `TRACING_ENABLED=false` (the default), `configure_tracing()` is a no-op
and all spans use the OTel **no-op tracer** — zero overhead.

### Span inventory

| Span name | Layer | Key attributes |
|---|---|---|
| `agent.invoke` | agent runtime | `request.id`, `agent.operation`, `session.id`, `result.success` |
| `mcp_adapter.get_macro_snapshot` | MCP adapter | `mcp.tool`, `request.id`, `macro.country`, `result.success` |
| `mcp_adapter.run_signal_engine` | MCP adapter | `mcp.tool`, `request.id`, `macro.country`, `signal.ids_count`, `result.success` |
| `mcp_tool.get_macro_features` | MCP tool | `mcp.tool`, `request.id`, `macro.country`, `indicator_count`, `macro.features_count`, `result.success` |
| `mcp_tool.get_macro_snapshot` | MCP tool | `mcp.tool`, `request.id`, `macro.country`, `macro.features_count`, `result.success` |
| `mcp_tool.run_signal_engine` | MCP tool | `mcp.tool`, `request.id`, `macro.country`, `signal.ids_count`, `signal.count`, `signal.engine_run_id`, `result.success` |
| `service.fetch_features` | macro service | `macro.country`, `macro.indicator_count`, `macro.source_id`, `macro.features_count` |
| `service.get_snapshot` | macro service | `macro.country`, `macro.source_id`, `macro.features_count` |
| `service.run_signal_engine` | signal service | `signal.definitions_count`, `signal.count` |
| `pipeline.ingest` | ingestion pipeline | `macro.country`, `macro.source_id`, `macro.indicator_count`, `pipeline.run_id`, `macro.features_count` |

### Span attribute safety rules

* **Never** include API keys, raw secrets, or authentication tokens as span attributes.
* **Never** include user-supplied free-text content (e.g. agent prompts or LLM outputs).
* **Safe attributes**: country codes, tool names, operation names, numeric counts, boolean success flags, and stable IDs (request_id, engine_run_id, pipeline_run_id).

All canonical attribute names are defined in `core/tracing/span_attributes.py`.

### Local Jaeger quickstart

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

TRACING_ENABLED=true OTLP_ENDPOINT=http://localhost:4318 python -m apps.api.main
# Open http://localhost:16686 to view traces
```

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
subsequent log record in the same async task carries these fields.  It also opens
an `agent.invoke` OTel span as the root span for the request.

### Fields bound automatically

| Field        | Source                         | Present when         |
|---|---|---|
| `trace_id`   | `set_trace_id()` (auto UUID)   | Always               |
| `request_id` | `request.request_id`           | Always               |
| `session_id` | `request.session_id`           | Non-empty session only |
| `otel_trace_id` | active OTel span context    | When a recording span is active |
| `otel_span_id`  | active OTel span context    | When a recording span is active |

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

> **Security note**: The FRED API key is **never** logged or traced. Only `series_id` and
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

OTel spans carry the same timing information and can be visualised in a trace
waterfall view in Jaeger or Grafana Tempo.

---

## Adding New Instrumentation

1. Import `get_logger` from `core.logging.logger` (not stdlib `logging`).
2. Import `get_tracer` from `core.tracing.tracer`.
3. Use `timed_operation("your_layer", "your_op", log)` around I/O or expensive
   calls.
4. Use `tracer.start_as_current_span("your_layer.your_op")` for OTel spans.
5. Set span attributes from `core.tracing.span_attributes` constants only.
6. Use keyword arguments for all structured fields (e.g. `log.info("event", key=value)`).
7. Never log or trace secrets, API keys, PII, or raw exception tracebacks as
   structured fields — use `log.exception()` only for unexpected errors.
