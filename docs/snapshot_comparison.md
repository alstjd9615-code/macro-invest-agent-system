# Snapshot Comparison

This document describes the snapshot comparison feature introduced in PR2.

---

## Overview

The comparison feature lets you diff a **current** macro snapshot against a
set of **prior** feature values.  All comparison logic is deterministic —
no LLM or speculative reasoning is involved.

Key guarantees:

* **Deterministic**: same inputs always produce the same output.
* **Explicit**: each change is captured as a typed `FeatureDelta`.
* **Bounded**: only indicators present in the current snapshot are compared.
* **Schema-valid**: success *and* failure responses are always schema-valid.
* **No speculation**: the comparison describes measured differences only.

---

## Architecture

```
SnapshotComparisonRequest
  (country, prior_snapshot_label, prior_features)
         │
         ▼
┌──────────────────────────────────────────┐
│  LangChainAgentRuntime / AgentRuntime    │
│  AgentOperation.COMPARE_SNAPSHOTS        │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  AgentService.compare_snapshots()        │
│  1. Guard: empty prior_features → error  │
│  2. MacroService.get_snapshot(country)   │ ← current snapshot (full domain object)
│  3. domain.compare_snapshots()           │ ← deterministic diff
│  4. format_comparison_summary()          │ ← deterministic string
└──────────────────┬───────────────────────┘
                   │
                   ▼
     SnapshotComparisonResponse
  (changed_count, unchanged_count, no_prior_count, summary)
```

---

## Domain Layer — `domain/macro/comparison.py`

### `PriorFeatureInput`

```python
class PriorFeatureInput(BaseModel, extra="forbid"):
    indicator_type: str   # e.g. "gdp", "inflation"
    value: float          # the prior indicator value
```

Minimal input contract for prior snapshot data.  Only `indicator_type` and
`value` are needed to compute a delta.

### `FeatureDelta`

```python
class FeatureDelta(BaseModel, extra="forbid"):
    indicator_type: str
    current_value: float
    prior_value: float | None    # None when direction="no_prior"
    delta: float | None          # current_value - prior_value; None when no_prior
    direction: "increased" | "decreased" | "unchanged" | "no_prior"
```

### `SnapshotComparison`

```python
class SnapshotComparison(BaseModel, extra="forbid"):
    country: str
    prior_snapshot_label: str
    current_snapshot_timestamp: datetime | None
    deltas: list[FeatureDelta]
    changed_count: int
    unchanged_count: int
    no_prior_count: int
```

### `compare_snapshots()`

```python
def compare_snapshots(
    current: MacroSnapshot,
    prior_features: list[PriorFeatureInput],
    prior_snapshot_label: str,
    country: str,
    unchanged_threshold: float = 1e-9,   # min |delta| to count as a change
) -> SnapshotComparison:
```

For each feature in `current`:
- Match to prior by `indicator_type` (first match wins).
- Compute `delta = current_value - prior_value`.
- If `abs(delta) <= unchanged_threshold` → `direction="unchanged"`.
- If `delta > 0` → `direction="increased"`.
- If `delta < 0` → `direction="decreased"`.
- No match → `direction="no_prior"`, `prior_value=None`, `delta=None`.

---

## Agent Layer

### Request — `SnapshotComparisonRequest`

```python
class SnapshotComparisonRequest(AgentRequest):
    country: str = "US"
    prior_snapshot_label: str           # required; e.g. "Q1-2026"
    prior_features: list[PriorFeatureInput] = []  # empty → prior-missing error
```

An **empty** `prior_features` list triggers the **prior-snapshot-missing**
failure path.  The response will be `success=False` with a clear error message.

### Response — `SnapshotComparisonResponse`

```python
class SnapshotComparisonResponse(AgentResponse):
    country: str = ""
    prior_snapshot_label: str = ""
    current_snapshot_timestamp: datetime | None = None
    changed_count: int = 0        # >= 0
    unchanged_count: int = 0      # >= 0
    no_prior_count: int = 0       # >= 0
    # inherited from AgentResponse:
    summary: str = ""
    success: bool
    error_message: str | None
```

All fields default to safe values so schema validation passes on the error path.

---

## Usage Example

```python
from agent.schemas import PriorFeatureInput, SnapshotComparisonRequest

# Build a request with known prior values.
request = SnapshotComparisonRequest(
    request_id="req-001",
    country="US",
    prior_snapshot_label="Q1-2026",
    prior_features=[
        PriorFeatureInput(indicator_type="gdp", value=3.2),
        PriorFeatureInput(indicator_type="inflation", value=4.1),
        PriorFeatureInput(indicator_type="unemployment", value=4.0),
    ],
)

result = await runtime.invoke(request)

if result.success:
    print(result.response.summary)
    print(f"Changed: {result.response.changed_count}")
    print(f"Unchanged: {result.response.unchanged_count}")
else:
    print(f"Error: {result.response.error_message}")
```

### Prior-snapshot-missing path

```python
# Empty prior_features → success=False
request = SnapshotComparisonRequest(
    request_id="req-002",
    country="US",
    prior_snapshot_label="missing-label",
    prior_features=[],   # triggers error path
)
result = await runtime.invoke(request)
assert result.success is False
assert "missing-label" in result.response.error_message
```

---

## Prompt Template

The LangChain runtime re-renders the comparison summary through a deterministic
prompt template.  The template describes the change counts without adding
interpretation or investment advice.

```python
from agent.prompts.templates import render_snapshot_comparison_summary

human_msg = render_snapshot_comparison_summary(
    country="US",
    prior_snapshot_label="Q1-2026",
    changed_count=2,
    unchanged_count=1,
    no_prior_count=0,
    context_summary="",   # optional session context hint
)
```

Context hints (from PR1) are appended to the **system** message only — never
the human message — and never override deterministic comparison results.

---

## Context Integration (PR1 + PR2)

When a `SnapshotComparisonRequest` carries a `session_id`, the runtime:

1. Injects the active session context hint into the system message.
2. Records the comparison turn in the session context, including:
   - `comparison_target = prior_snapshot_label` in `AnalysisParameters`
   - `country` in `AnalysisParameters`

This allows follow-up turns to reference the prior label without repeating it.

---

## Failure Paths

| Condition | `success` | `error_message` |
|---|---|---|
| `prior_features=[]` | `False` | Mentions the prior label and instructs to supply `prior_features` |
| `MacroService.get_snapshot()` raises | `False` | Wraps the exception detail |
| Schema validation fails | `False` | Raised as `OutputValidationError` by the runtime boundary |

---

## Design Constraints

| Constraint | Detail |
|---|---|
| Deterministic | `compare_snapshots()` is a pure function |
| No speculation | Deltas are arithmetic differences only |
| Schema-valid on all paths | Defaults on every field ensure `success=False` responses are always valid |
| No comparison logic in prompts | Templates only format pre-computed counts; no reasoning |
| Explicit prior data | Caller must supply `prior_features`; no automatic prior lookup |
| Reuses existing snapshot structures | `MacroSnapshot`, `MacroFeature`, `MacroService.get_snapshot()` |

---

## Testing

| File | Covers |
|---|---|
| `tests/unit/domain/macro/test_comparison.py` | `compare_snapshots()` — no-change, change-detected, prior-missing, partial prior, threshold, first-match-wins, metadata |
| `tests/unit/agent/test_comparison_formatting.py` | `format_comparison_summary()`, `format_comparison_error()`, `format_prior_missing_error()` |
| `tests/unit/agent/test_comparison_service.py` | `AgentService.compare_snapshots()` — happy path, prior-missing, fetch-failure, schema validity |
| `tests/unit/agent/test_comparison_runtime.py` | `AgentRuntime` + `LangChainAgentRuntime` dispatch, `validate_snapshot_comparison_response`, prompt template |
