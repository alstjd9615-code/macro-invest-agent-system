# Phase 2 — LangChain Agent Runtime

This document describes the Phase 2 integration that wires the existing
read-only agent service into a lightweight LangChain runtime with prompt
templates, tool bindings, and output schema validation.

---

## Overview

Phase 2 adds a `LangChainAgentRuntime` that wraps `AgentService` with:

1. **Prompt templates** — LangChain `ChatPromptTemplate` objects for signal
   review and macro snapshot summary formatting.
2. **Tool bindings** — MCP adapter methods wrapped as LangChain
   `StructuredTool` objects.
3. **Output validation** — schema enforcement at the runtime boundary.
4. **Conversation context** (optional) — session-scoped, in-memory
   recent-turn carryover.

The runtime preserves all Phase 1 constraints: read-only, deterministic,
no LLM calls, no business logic in the runtime layer, and no MCP boundary
bypass.

---

## Architecture

```
Caller
  │
  │  AgentRequest
  ▼
┌──────────────────────────────┐
│   LangChainAgentRuntime      │ ← prompt templates + validation
│                              │
│  ┌────────────────────────┐  │
│  │  Prompt Templates      │  │  ChatPromptTemplate (signal review,
│  │  (agent/prompts/)      │  │  snapshot summary)
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │  Tool Bindings         │  │  StructuredTool wrappers over
│  │  (agent/runtime/tools) │  │  MCPAdapter methods
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │  Output Validation     │  │  Schema enforcement at boundary
│  │  (output_validation)   │  │
│  └────────────────────────┘  │
│                              │
│  ┌────────────────────────┐  │
│  │  Conversation Context  │  │  Optional in-memory turn history
│  │  (session-scoped)      │  │
│  └────────────────────────┘  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       AgentService           │ ← unchanged from Phase 1
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       MCPAdapter             │ ← unchanged
└──────────────┬───────────────┘
               │
               ▼
         MCP Tool Handlers
```

---

## New Modules

### `agent/prompts/templates.py`

LangChain `ChatPromptTemplate` objects for each agent operation.

| Template | Variables |
|---|---|
| `SIGNAL_REVIEW_PROMPT` | `signal_ids`, `country`, `signals_generated`, `buy_signals`, `sell_signals`, `hold_signals`, `dominant_direction`, `engine_run_id`, `execution_time_ms` |
| `SNAPSHOT_SUMMARY_PROMPT` | `country`, `features_count`, `snapshot_timestamp` |

Each template includes a **system message** (tone/constraints) and a **human
message** (data template).  Two helper functions render templates to plain
strings:

- `render_signal_review_summary(**kwargs) → str`
- `render_snapshot_summary(**kwargs) → str`

Templates are rendered directly (no LLM call) in the current implementation.
When an LLM is added, the same `ChatPromptTemplate` objects can be passed to a
chat model without modification.

---

### `agent/runtime/tools.py`

MCP adapter methods wrapped as LangChain `StructuredTool` objects.

| Tool | MCP Adapter Method | Input Schema |
|---|---|---|
| `run_signal_engine` | `MCPAdapter.run_signal_engine` | `RunSignalEngineInput` |
| `get_macro_snapshot` | `MCPAdapter.get_macro_snapshot` | `GetMacroSnapshotInput` |

Tools are created via factory functions:

```python
create_signal_engine_tool(adapter) → StructuredTool
create_macro_snapshot_tool(adapter) → StructuredTool
```

All tools are read-only and honour the existing MCP boundary.

---

### `agent/runtime/output_validation.py`

Schema validation enforced at the runtime boundary.

| Function | Scope |
|---|---|
| `validate_agent_response(response)` | Round-trip validation for any `AgentResponse` |
| `validate_signal_review_response(response)` | Above + `signals_generated == buy + sell + hold` |
| `validate_snapshot_summary_response(response)` | Round-trip validation for snapshot responses |
| `validate_runtime_result(result)` | Envelope + inner response validation |

Raises `OutputValidationError` on any schema violation.

---

### `agent/runtime/langchain_runtime.py`

The `LangChainAgentRuntime` class.

```python
from agent.runtime.langchain_runtime import LangChainAgentRuntime

runtime = LangChainAgentRuntime(
    service=agent_service,
    adapter=mcp_adapter,
    enable_context=True,      # optional
    max_context_turns=10,     # optional
)

result = await runtime.invoke(request)
```

**Pipeline steps:**

1. Delegate to `AgentService` for deterministic tool execution.
2. Re-format the `summary` field using the LangChain prompt template.
3. Validate the complete result against the output schema.
4. (Optional) Record the turn in the conversation context.

---

### `ConversationContext` and `ConversationTurn`

Session-scoped, in-memory conversation context for recent-turn carryover.

- FIFO eviction when `max_turns` is exceeded.
- No database persistence, no retrieval memory, no user profile memory.
- Stores: request type, serialised request snapshot, response summary, success
  flag.

---

## Design Constraints

| Constraint | Detail |
|---|---|
| Read-only | No MCP tool called by the runtime modifies state |
| Deterministic | Prompt templates are rendered directly; no LLM is invoked |
| Prompts don't override tools | Templates only format tool outputs; they never reinterpret signal results |
| Schema-safe | Every output is validated via `validate_runtime_result` before return |
| MCP boundary preserved | Tools delegate through `MCPAdapter` → MCP handler → service |
| No autonomous loops | Each `invoke` call is a single request → response |
| No write actions | No mutation of any state |
| No long-term memory | Context is in-memory, session-scoped, and capped |

---

## Extension Path

### Adding an LLM

1. Add `langchain-openai` (or another provider) as a dependency.
2. Create a chat model instance in `LangChainAgentRuntime.__init__`.
3. Pass `SIGNAL_REVIEW_PROMPT` / `SNAPSHOT_SUMMARY_PROMPT` to the model
   instead of rendering directly.
4. The deterministic formatters remain as fallbacks for tests and CI.

### Adding LangGraph

1. Add `langgraph` as a dependency.
2. Define a `StateGraph` with nodes for routing, tool invocation, formatting,
   and validation.
3. Replace or extend `LangChainAgentRuntime.invoke` with the graph executor.
4. `AgentService` and the MCP adapter remain unchanged.

### Adding new operations

Follow the existing pattern:

1. Add a new prompt template to `agent/prompts/templates.py`.
2. Add a new tool factory to `agent/runtime/tools.py`.
3. Add a new dispatcher method to `LangChainAgentRuntime`.
4. Add validation logic to `output_validation.py`.
5. Add tests.

---

## Testing

Unit tests for the Phase 2 modules live in:

| File | Covers |
|---|---|
| `tests/unit/agent/test_prompt_templates.py` | Template structure, rendering, determinism |
| `tests/unit/agent/test_output_validation.py` | Schema validation, domain invariants, error types |
| `tests/unit/agent/test_langchain_runtime.py` | End-to-end dispatch, prompt formatting, tool bindings, context |

All tests are async-first and follow the existing test patterns.
