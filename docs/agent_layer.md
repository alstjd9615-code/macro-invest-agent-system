# Agent Layer — Read-Only Boundary

This document describes the read-only agent layer.
It explains the boundary contract, available operations, module structure, data
flow, and extension path for future LangChain / LangGraph integration.

---

## Overview

The agent layer sits above the MCP tool layer and below any future LLM
integration.  Its job is to **orchestrate MCP tool calls** and return
**schema-validated summaries**.

```
Caller / Test
     │
     │  AgentRequest (validated Pydantic model)
     ▼
┌─────────────────────────────┐
│       AgentRuntime          │  ← optional; future LangChain/LangGraph hook
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       AgentService          │  ← thin; no business logic
└──────────────┬──────────────┘
               │
    ┌──────────┴─────────┐
    ▼                    ▼
┌────────────┐  ┌─────────────────────┐
│ summaries  │  │      errors         │
│ (format)   │  │  (format)           │
└────────────┘  └─────────────────────┘
               │
               ▼
┌─────────────────────────────┐
│       MCPAdapter            │  ← raises MCPToolError on failure
└──────────────┬──────────────┘
               │  MCPRequest / MCPResponse
               ▼
┌─────────────────────────────┐
│     MCP Tool Handlers       │  ← never raise; return success/error
└──────────────┬──────────────┘
               │
               ▼
       Service / Domain layers
```

---

## Read-Only Boundary

The agent layer is **strictly read-only**:

| Constraint | Detail |
|---|---|
| No writes | No MCP tool called by the agent modifies state |
| No autonomous loops | Each operation is a single request → response |
| No memory persistence | No state is stored between calls |
| No multi-agent calls | `AgentService` is a single, flat orchestrator |
| No direct domain access | All data flows through the MCP adapter |
| No LLM calls | Summaries are deterministic; no external model is invoked |

---

## Modules

### `agent/schemas.py` — Typed I/O Models

| Class | Description |
|---|---|
| `AgentRequest` | Base request with `request_id` (non-empty) and `timestamp` |
| `SignalReviewRequest` | Request a review of one or more signal IDs; validates non-empty `signal_ids` |
| `MacroSnapshotSummaryRequest` | Request a summary of the current macro snapshot |
| `AgentResponse` | Base response; validates that `error_message` is set when `success=False` |
| `SignalReviewResponse` | Extends `AgentResponse` with engine metadata; all count fields are `ge=0` |
| `MacroSnapshotSummaryResponse` | Extends `AgentResponse` with snapshot metadata; `features_count` is `ge=0` |

All response fields have safe defaults so schema validation passes on error paths too.

#### Added field validators

| Model | Validator | Rule |
|---|---|---|
| `SignalReviewRequest` | `signal_ids_must_be_non_empty_strings` | Each ID must be a non-empty, stripped string |
| `AgentRequest` | `request_id` field | Must be at least one character |
| `AgentResponse` | `error_message_present_on_failure` | `error_message` must be set when `success=False` |
| `SignalReviewResponse` | count fields | `signals_generated`, `buy_signals`, `sell_signals`, `hold_signals` are `ge=0` |
| `SignalReviewResponse` | `execution_time_ms` | `ge=0.0` |
| `MacroSnapshotSummaryResponse` | `features_count` | `ge=0` |

---

### `agent/formatting/` — Formatting Concerns

Summary and error formatting have been separated from `AgentService` into
their own module so each concern can be tested and evolved independently.

#### `agent/formatting/summaries.py`

| Function | Description |
|---|---|
| `dominant_signal_type(response)` | Returns `"BUY"`, `"SELL"`, `"HOLD"`, or `"none"` based on signal counts |
| `format_signal_review_summary(response, signal_ids, country)` | Builds the deterministic signal review summary string |
| `format_snapshot_summary(response, country)` | Builds the deterministic macro snapshot summary string |

All functions are pure (no side effects, no I/O) and fully deterministic.

#### `agent/formatting/errors.py`

| Function | Description |
|---|---|
| `format_signal_review_error(raw_error, request_id)` | Returns a user-facing error message for a failed signal review |
| `format_snapshot_summary_error(raw_error, request_id, country)` | Returns a user-facing error message for a failed snapshot summary |

Error messages include the `request_id` and `country` for tracing but omit
low-level implementation details.  The raw MCP error is forwarded as `Detail:`
so callers that need the original message can still find it.

---

### `agent/prompts/` — Template Documentation

| File | Description |
|---|---|
| `signal_review.md` | Documents the deterministic template used for signal review summaries |
| `snapshot_summary.md` | Documents the deterministic template used for macro snapshot summaries |

These files record the current output format and are the intended reference
when a future LLM-backed formatting stage is introduced.

---

### `agent/mcp_adapter.py` — MCP Tool Invocation

The `MCPAdapter` wraps MCP tool handlers to provide a **raise-on-failure** interface:

- On `MCPResponse.success=True` → the MCP response is returned as-is.
- On `MCPResponse.success=False` → `MCPToolError` is raised with `tool_name` and `error_message`.

This design lets `AgentService` handle all failure modes in one `except MCPToolError` block
rather than scattering `if not response.success` checks throughout.

**Available adapter methods:**

| Method | MCP Tool Invoked |
|---|---|
| `get_macro_snapshot(request_id, country)` | `handle_get_macro_snapshot` |
| `run_signal_engine(request_id, signal_ids, country)` | `handle_run_signal_engine` |

---

### `agent/service.py` — Agent Service

`AgentService` provides two public async methods:

#### `review_signals(request: SignalReviewRequest) → SignalReviewResponse`

1. Calls `MCPAdapter.run_signal_engine` with the requested signal IDs.
2. On success: delegates to `format_signal_review_summary` and populates `SignalReviewResponse`.
3. On `MCPToolError`: delegates to `format_signal_review_error` and returns `SignalReviewResponse(success=False)`.

**Response fields**

| Field | Source |
|---|---|
| `engine_run_id` | Forwarded from `RunSignalEngineResponse` |
| `signals_generated` | Forwarded from `RunSignalEngineResponse` |
| `buy_signals` | Forwarded from `RunSignalEngineResponse` |
| `sell_signals` | Forwarded from `RunSignalEngineResponse` |
| `hold_signals` | Forwarded from `RunSignalEngineResponse` |
| `execution_time_ms` | Forwarded from `RunSignalEngineResponse` |
| `summary` | Deterministic text from `agent.formatting.summaries.format_signal_review_summary` |
| `error_message` | User-facing text from `agent.formatting.errors.format_signal_review_error` (on failure) |

---

#### `summarize_macro_snapshot(request: MacroSnapshotSummaryRequest) → MacroSnapshotSummaryResponse`

1. Calls `MCPAdapter.get_macro_snapshot` for the requested country.
2. On success: delegates to `format_snapshot_summary` and populates `MacroSnapshotSummaryResponse`.
3. On `MCPToolError`: delegates to `format_snapshot_summary_error` and returns `MacroSnapshotSummaryResponse(success=False)`.

**Response fields**

| Field | Source |
|---|---|
| `country` | Echoed from `request.country` |
| `snapshot_timestamp` | Forwarded from `GetMacroSnapshotResponse` |
| `features_count` | Forwarded from `GetMacroSnapshotResponse` |
| `summary` | Deterministic text from `agent.formatting.summaries.format_snapshot_summary` |
| `error_message` | User-facing text from `agent.formatting.errors.format_snapshot_summary_error` (on failure) |

---

### `agent/runtime/` — Runtime Adapter

See [`docs/agent_runtime.md`](agent_runtime.md) for full documentation.

`AgentRuntime` is a lightweight adapter over `AgentService` that:

- Provides a single `invoke` entry-point for both agent operations.
- Returns a typed `AgentRuntimeResult` with an `operation` label.
- Is the **recommended integration point** for future LangChain / LangGraph wiring.

---

## Error Handling

Tool failures are surfaced as `MCPToolError` by the adapter and converted to
a failed `AgentResponse` by the service.  The caller **never receives an
uncaught exception** — every code path returns a schema-valid response object.

The `error_message` field now contains a **user-facing** error string produced
by `agent.formatting.errors`.  The message includes:

* A human-readable description of what could not be completed.
* The `request_id` for tracing.
* A `Detail:` suffix with the raw MCP error for diagnostics.

| Failure scenario | `success` | `error_message` |
|---|---|---|
| Unknown signal ID | `False` | "Signal review could not be completed … Detail: …" |
| Macro snapshot unavailable | `False` | "Macro snapshot for country=… could not be retrieved … Detail: …" |
| Signal engine failure | `False` | "Signal review could not be completed … Detail: …" |
| Empty `signal_ids` list | `False` (validation) | Pydantic `ValidationError` before the service is called |

---

## Usage Example

```python
import asyncio
from agent.service import AgentService
from agent.runtime import AgentRuntime
from agent.schemas import SignalReviewRequest, MacroSnapshotSummaryRequest
from services.macro_service import MacroService
from services.signal_service import SignalService

service = AgentService(MacroService(), SignalService())
runtime = AgentRuntime(service)

async def main() -> None:
    # Signal review via runtime
    result = await runtime.invoke(
        SignalReviewRequest(
            request_id="req-001",
            signal_ids=["bull_market", "recession_warning"],
        )
    )
    if result.success:
        print(result.response.summary)
    else:
        print(f"Error: {result.error_message}")

    # Macro snapshot summary via service directly
    snapshot = await service.summarize_macro_snapshot(
        MacroSnapshotSummaryRequest(request_id="req-002", country="US")
    )
    if snapshot.success:
        print(snapshot.summary)
    else:
        print(f"Error: {snapshot.error_message}")

asyncio.run(main())
```

---

## Extension Points

### Adding a new agent operation

1. Add a new `*Request` / `*Response` pair to `agent/schemas.py`.
2. Add a formatter function to `agent/formatting/summaries.py` (and optionally `errors.py`).
3. Add a prompt template to `agent/prompts/`.
4. Add a new adapter method to `MCPAdapter` (or reuse existing ones).
5. Add a new method to `AgentService` following the
   `try adapter call → format → return` pattern.
6. Add a new `AgentOperation` entry and dispatcher to `AgentRuntime`.
7. Add unit tests covering the happy path, at least one tool failure, and schema validity.

### Injecting a custom registry

Pass a `SignalRegistry` instance to `AgentService.__init__` to override the
built-in signal definitions.  This is useful in tests and evaluation harnesses.

### LangChain / LangGraph integration

Subclass or replace `AgentRuntime` without touching `AgentService` or the MCP
adapter.  See [`docs/agent_runtime.md`](agent_runtime.md) for details.

---

## Out of Scope (This Version)

- 🚫 LLM-generated summaries
- 🚫 Memory or state persistence between calls
- 🚫 Multi-agent orchestration
- 🚫 Write-capable operations
- 🚫 Autonomous loops or long-running plans
- 🚫 Direct domain-layer access (always via MCP)

