# Backlog: 0402 — Structured Narrative Explanations (Phase 3 bridge)

**Priority:** P1  
**Workstream:** Multi-Engine Analysis Hub — AI Explanation Engine (deterministic layer)  
**Status:** ✅ Implemented

---

## Scope

Replace debug-string explanations with analyst-facing structured narratives
grounded in the macro regime.  Add `caveats[]` and `data_quality_notes[]`
to `ExplanationResponse` to make data quality state explicit.

## Implementation scope

| File | Change |
|---|---|
| `domain/macro/narrative_builder.py` | New: `build_regime_narrative(regime)` — produces `summary`, `rationale_points`, `caveats`, `data_quality_notes`, `regime_context` |
| `apps/api/dto/explanations.py` | Added `caveats: list[str]`, `data_quality_notes: list[str]` to `ExplanationResponse`; documented minimum `regime_context` keys |
| `apps/api/routers/explanations.py` | New route: `GET /api/explanations/regime/latest`; updated `build_and_register_explanation` with optional `regime_label`/`regime_context` |
| `apps/api/routers/signals.py` | Signal explanations include both regime narrative (environment) and asset-level rationale (per-signal) |

## ExplanationResponse structure

```json
{
  "explanation_id": "regime:<id>",
  "summary": "<multi-sentence analyst narrative>",
  "rationale_points": ["<state bullet>", ...],
  "caveats": ["<interpretation limit>", ...],
  "data_quality_notes": ["<data warning>", ...],
  "regime_label": "slowdown",
  "regime_context": {
    "label": "slowdown",
    "family": "downshift",
    "confidence": "medium",
    "transition": "initial",
    "freshness": "fresh",
    "degraded_status": "none",
    ...
  },
  "generated_at": "<ISO 8601>",
  "trust": { ... }
}
```

## Minimum `regime_context` keys (documented)

| Key | Description |
|---|---|
| `label` | Regime label value |
| `family` | Regime family value |
| `confidence` | Confidence level |
| `transition` | Transition type |
| `freshness` | Data freshness status |
| `degraded_status` | Data degraded status |

## Caveat rules

Caveats are generated when:
- Transition type is `initial` (no prior baseline)
- Confidence is `LOW`
- Regime is `MIXED` or `UNCLEAR`
- Missing inputs list is non-empty

## Data quality note rules

Data quality notes are generated when:
- Freshness is not `FRESH`
- Degraded status is not `NONE`
- Missing inputs list is non-empty
- Regime was seeded by the bootstrap seeder (`metadata.seeded == "true"`)

## Acceptance criteria (all met)

- [x] `/api/explanations/regime/latest` returns 200 with `summary`, `rationale_points`, `regime_context`
- [x] Explanation reflects regime label, confidence, transition, supporting states, data quality
- [x] `caveats[]` and `data_quality_notes[]` are explicitly separated
- [x] Signal explanation includes both regime-level context AND asset-level rationale
- [x] `regime_context` minimum keys are documented in DTO docstring
- [x] Bootstrap/seeded data is flagged in `data_quality_notes`
- [x] Explanation is NOT just a re-statement of regime label

## Tests

- `tests/unit/domain/macro/test_narrative_builder.py` — 22 tests
- `tests/unit/api/test_explanations_router.py` — 6 tests (all existing pass)

## Remaining risks / follow-up

- Narratives are currently deterministic/template-based. Phase 4 will
  introduce an LLM-backed AI Explanation Engine for dynamic narrative generation.
- `caveats` text is hardcoded; future work should drive caveats from a
  configurable caveat policy.
- Signal-level explanation is registered in-memory; no persistence. A
  future explanation persistence layer is needed for audit/replay.
