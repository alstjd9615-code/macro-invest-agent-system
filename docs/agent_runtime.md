# Agent Runtime Adapter

This document describes `agent/runtime/agent_runtime.py` — the lightweight
runtime adapter introduced to provide a clean, extensible entry-point for
agent operation dispatch and to serve as the future integration point for
LangChain / LangGraph.

---

## Overview

`AgentRuntime` is a thin stateless wrapper around `AgentService`.  It:

1. Accepts any supported agent request via a single `invoke` entry-point.
2. Infers the operation type from the request type.
3. Delegates to the correct `AgentService` method.
4. Returns a typed `AgentRuntimeResult` envelope with an `operation` label.

The runtime layer does **not** contain business logic.  It is purely a
dispatch and result-normalisation wrapper.

---

## Classes

### `AgentOperation` (enum)

```python
class AgentOperation(str, Enum):
    REVIEW_SIGNALS = "review_signals"
    SUMMARIZE_MACRO_SNAPSHOT = "summarize_macro_snapshot"
```

An enumeration of the operations supported by `AgentRuntime`.  Each value
corresponds to a method on `AgentService`.

---

### `AgentRuntimeResult`

```python
class AgentRuntimeResult(BaseModel, extra="forbid"):
    operation: AgentOperation
    response: SignalReviewResponse | MacroSnapshotSummaryResponse
```

A Pydantic model that wraps an agent response with a typed `operation` label.

**Convenience properties:**

| Property | Type | Description |
|---|---|---|
| `success` | `bool` | Proxies `response.success` |
| `error_message` | `str \| None` | Proxies `response.error_message` |

---

### `AgentRuntime`

The primary class.  Constructed with an `AgentService` instance.

```python
runtime = AgentRuntime(AgentService(MacroService(), SignalService()))
result = await runtime.invoke(request)
```

**Method:** `invoke(request) → AgentRuntimeResult`

| Request type | Operation dispatched | Response type |
|---|---|---|
| `SignalReviewRequest` | `review_signals` | `SignalReviewResponse` |
| `MacroSnapshotSummaryRequest` | `summarize_macro_snapshot` | `MacroSnapshotSummaryResponse` |
| Any other type | — | `TypeError` raised |

The `invoke` method **never raises** for tool failures — those are converted to
`AgentRuntimeResult(success=False)` by the underlying `AgentService`.
`TypeError` is only raised if an unsupported request type is passed.

---

## Usage Example

```python
import asyncio
from agent.runtime import AgentRuntime, AgentOperation
from agent.schemas import SignalReviewRequest, MacroSnapshotSummaryRequest
from agent.service import AgentService
from services.macro_service import MacroService
from services.signal_service import SignalService

service = AgentService(MacroService(), SignalService())
runtime = AgentRuntime(service)

async def main() -> None:
    result = await runtime.invoke(
        SignalReviewRequest(
            request_id="req-001",
            signal_ids=["bull_market"],
        )
    )
    assert result.operation == AgentOperation.REVIEW_SIGNALS
    if result.success:
        print(result.response.summary)
    else:
        print(f"Error: {result.error_message}")

asyncio.run(main())
```

---

## Design Constraints

| Constraint | Detail |
|---|---|
| Read-only | `invoke` only dispatches to read-only `AgentService` methods |
| Stateless | No session state, memory, or side effects between calls |
| No LLM calls | Current implementation is fully deterministic |
| Schema-safe | `AgentRuntimeResult` is validated; all paths return schema-valid output |

---

## Future Extension (LangChain / LangGraph)

`AgentRuntime` is the **recommended integration point** for introducing
LangChain chains or LangGraph graphs.  Two patterns are supported:

### 1. Subclass and override `invoke`

```python
from agent.runtime.agent_runtime import AgentRuntime, AgentRuntimeResult, AgentRequestInput

class LangChainAgentRuntime(AgentRuntime):
    async def invoke(self, request: AgentRequestInput) -> AgentRuntimeResult:
        # inject chain-of-thought, tool selection, memory, etc.
        ...
        return await super().invoke(request)
```

This keeps `AgentService` and the MCP adapter completely unchanged.

### 2. Replace `AgentRuntime` with a LangGraph graph

Implement the same `invoke(request) → AgentRuntimeResult` interface in a
LangGraph node and swap the runtime instance.  `AgentService` and all
downstream layers remain unchanged.

In both cases the deterministic formatters in `agent/formatting/` remain
available as fallbacks when no LLM is configured (e.g. in unit tests and CI).

---

## Testing

Unit tests for `AgentRuntime` live in
`tests/unit/agent/test_runtime.py`.  They cover:

- Correct `operation` label for each request type.
- Correct response type for each request type.
- `success` / `error_message` proxy properties.
- `TypeError` on unsupported request types.
- Schema validity of `AgentRuntimeResult` on success and failure paths.
