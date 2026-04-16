# Conversation Context

This document describes the session-scoped, in-memory conversation context
system introduced in PR1 (`agent/context/`).

---

## Overview

The context system enables lightweight follow-up handling within a single
analysis session.  It:

1. Stores up to `max_turns` recent conversation turns per session (FIFO eviction).
2. Carries active analysis parameters — country, timeframe, signal type,
   comparison target — forward across turns so they do not need to be
   repeated in every request.
3. Injects a compact context hint into the system message of the prompt
   template to make the active context visible to the formatter.
4. Never overrides or reinterprets deterministic tool results.

Context is **in-memory only**.  It does not persist beyond the process
lifetime and never crosses session boundaries.

---

## Architecture

```
Caller (with optional session_id)
  │
  ▼
┌──────────────────────────────┐
│  LangChainAgentRuntime       │
│                              │
│  _resolve_context(request)   │ ──► InMemoryContextStore.get_or_create(session_id)
│         │                    │         (or per-instance ConversationContext
│         │                    │          when enable_context=True and no session_id)
│         ▼                    │
│  ConversationContext         │
│   .context_summary() ──────► │ context_hint (injected into system message)
│                              │
│  delegate to AgentService    │ ← deterministic tool results (unchanged)
│                              │
│  record turn ──────────────► │ ConversationContext.add_turn(...)
└──────────────────────────────┘
```

---

## Modules

### `agent/context/models.py`

Defines the three core types.

#### `AnalysisParameters`

```python
class AnalysisParameters(BaseModel, extra="forbid"):
    country: str | None
    timeframe: str | None
    signal_type: str | None
    comparison_target: str | None
```

Carries the active analysis parameters across turns.

| Method | Description |
|---|---|
| `merge(prior)` | Returns a new instance combining `self` (overrides) with `prior` (fallback for `None` fields). |
| `is_empty()` | `True` when all fields are `None`. |
| `as_context_hint()` | Returns a compact string like `"country=US, signal_type=BUY"` for prompt injection. |

#### `ConversationTurn`

```python
class ConversationTurn(BaseModel, extra="forbid"):
    request_type: str
    request_snapshot: dict[str, Any]
    response_summary: str          # default ""
    success: bool                  # default True
    active_parameters: AnalysisParameters  # default empty
```

Immutable record of a single request–response cycle.

#### `ConversationContext`

```python
ctx = ConversationContext(max_turns=10)
ctx.add_turn(turn)
hint = ctx.context_summary()
ctx.clear()
```

Session-scoped, in-memory container.  Stores turns in a `deque` with FIFO
eviction.  The `active_parameters` property returns the current merged
parameter set, and `context_summary()` produces the prompt hint string.

---

### `agent/context/store.py`

Provides the `ContextStore` protocol and the `InMemoryContextStore` implementation.

#### `ContextStore` (Protocol)

```python
@runtime_checkable
class ContextStore(Protocol):
    def get_or_create(self, session_id: str, max_turns: int = 10) -> ConversationContext: ...
    def get(self, session_id: str) -> ConversationContext | None: ...
    def clear(self, session_id: str) -> None: ...
```

#### `InMemoryContextStore`

```python
store = InMemoryContextStore()
ctx = store.get_or_create("session-abc", max_turns=5)
ctx.add_turn(...)

# Same session ID retrieves the same context object.
same_ctx = store.get_or_create("session-abc")
assert same_ctx is ctx

# A different session ID gets a fresh, independent context.
other_ctx = store.get_or_create("session-xyz")
assert other_ctx is not ctx

# Check if a session exists without creating it.
assert store.get("never-seen") is None

# Remove a session (safe if session does not exist).
store.clear("session-abc")
```

Session isolation is guaranteed: data written to one session ID is never
visible from another.

---

### `agent/context/trimming.py`

Pure functions for bounding and filtering turn lists.

| Function | Description |
|---|---|
| `trim_to_max_turns(turns, max_turns)` | Keep only the `max_turns` most-recent turns (FIFO). Raises `ValueError` if `max_turns < 1`. |
| `keep_successful_only(turns)` | Filter to turns where `success is True`. |
| `extract_recent_summaries(turns, limit=3)` | Return the last `limit` non-empty `response_summary` strings. Raises `ValueError` if `limit < 1`. |

All functions are pure (no mutation of the input list).

---

## Integration — `LangChainAgentRuntime`

`LangChainAgentRuntime` integrates the context system via two modes:

### Mode 1: Session-keyed (recommended)

Pass a non-empty `session_id` on any `AgentRequest` subclass.  The runtime
creates or retrieves the matching `ConversationContext` from its internal
`InMemoryContextStore`.

```python
from agent.schemas import MacroSnapshotSummaryRequest

result = await runtime.invoke(
    MacroSnapshotSummaryRequest(
        request_id="req-001",
        country="US",
        session_id="my-session",       # enables session-scoped context
    )
)
```

Each `session_id` has a completely independent context.  Passing a different
`session_id` — or omitting it — never reads from another session's context.

### Mode 2: Legacy per-instance (optional)

Construct the runtime with `enable_context=True`.  Requests that carry no
`session_id` use a single shared `ConversationContext` owned by the runtime
instance.

```python
runtime = LangChainAgentRuntime(
    service=agent_service,
    adapter=mcp_adapter,
    enable_context=True,
    max_context_turns=10,
)
```

### Prompt injection

When context exists, `ConversationContext.context_summary()` is appended to
the system message as a read-only hint:

```
[Session context: Active parameters: country=US. Recent turns: [1] MacroSnapshotSummaryRequest (ok): Macro snapshot for country=US...]
```

This never replaces or overrides the deterministic tool output — only the
system message changes.

---

## Design Constraints

| Constraint | Detail |
|---|---|
| Session-scoped only | Context lives at the runtime layer; `AgentService` and `MCPAdapter` are stateless |
| In-memory | No database, file system, or external store |
| Bounded | Hard `max_turns` cap with FIFO eviction; no unbounded growth |
| Explicit | Context represented as typed Pydantic models, not implicit shared mutable state |
| Read-only | Context never overrides deterministic tool results |
| No cross-session sharing | Each `session_id` maps to an isolated `ConversationContext` |
| No long-term memory | All context is lost on process restart |
| No user profiling | Context holds only analysis parameters and turn summaries |

---

## Non-goals

The following are **explicitly out of scope** for this system:

* Database-backed conversation persistence
* Long-term or retrieval memory
* Vector search over past turns
* Cross-session personalization
* User profiling

---

## Testing

Unit tests for the context system live in:

| File | Covers |
|---|---|
| `tests/unit/agent/test_context_models.py` | `AnalysisParameters`, `ConversationTurn`, `ConversationContext` — all paths |
| `tests/unit/agent/test_context_store.py` | `InMemoryContextStore` — session isolation, protocol conformance, missing context path |
| `tests/unit/agent/test_context_trimming.py` | `trim_to_max_turns`, `keep_successful_only`, `extract_recent_summaries` |
| `tests/unit/agent/test_langchain_runtime.py` | Session-scoped context via `session_id`, context accumulation, session isolation, bounded turns, tool-result immutability |

The test suite covers the following paths:

* **Happy path** — context records, merges parameters, and injects hint correctly.
* **Missing context path** — stateless requests (no `session_id`, `enable_context=False`) complete without error.
* **Bounded trimming** — FIFO eviction keeps `turn_count <= max_turns`.
* **Context isolation** — mutations in one session do not affect any other session.
* **Failure path** — failed turns are recorded with `success=False`; responses remain schema-valid.
