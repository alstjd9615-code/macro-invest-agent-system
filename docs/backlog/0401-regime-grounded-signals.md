# Backlog: 0401 — Regime-Grounded Signal Rules (Phase 3 bridge)

**Priority:** P0  
**Workstream:** Multi-Engine Analysis Hub — Rule-Based Macro Engine  
**Status:** ✅ Implemented

---

## Scope

Replace the placeholder snapshot-based signal engine with a deterministic
regime-grounded signal rule table.  Each `RegimeLabel` maps to a list of
structured `RegimeSignalRule` objects.

## Implementation scope

| File | Change |
|---|---|
| `domain/signals/regime_signal_rules.py` | New: `RegimeSignalRule` dataclass + `REGIME_SIGNAL_MAP` + `get_regime_signal_rules()` |
| `domain/signals/models.py` | Added `asset_class`, `supporting_regime`, `supporting_drivers`, `conflicting_drivers` to `SignalOutput` |
| `apps/api/dto/signals.py` | Added same fields to `SignalSummaryDTO` |
| `apps/api/dto/builders.py` | Updated `signal_output_to_dto()` to map new fields |
| `apps/api/dto/trust.py` | Added `degraded_reason: str | None` to `TrustMetadata` |
| `services/signal_service.py` | Added `run_regime_grounded_engine(regime)` method |
| `apps/api/routers/signals.py` | Regime-grounded path first; fallback with `degraded_reason` |

## Signal structure per rule

Each `RegimeSignalRule` carries:
- `asset_class`         — target asset class
- `signal_direction`    — BUY / SELL / HOLD / NEUTRAL
- `signal_strength`     — VERY_WEAK … VERY_STRONG
- `signal_confidence`   — numeric 0.0–1.0 (regime-level conviction)
- `supporting_regime`   — regime label text
- `supporting_drivers`  — macro factors supporting the signal
- `conflicting_drivers` — macro factors reducing confidence
- `regime_rationale`    — analyst-facing narrative (reusable by explanation layer)

## Regime coverage

All 9 `RegimeLabel` values are covered.  Conceptual framework cross-reference:

| RegimeLabel | Conceptual equivalent |
|---|---|
| GOLDILOCKS | Classic Expansion / Goldilocks |
| REFLATION | Policy Easing Transition / Reflationary Recovery |
| DISINFLATION | Disinflation Slowdown |
| STAGFLATION_RISK | Stagflation Risk |
| CONTRACTION | Recessionary Contraction |
| POLICY_TIGHTENING_DRAG | Overheating Response / Tightening Drag |
| SLOWDOWN | Late-Cycle Slowdown |
| MIXED | Conflicting Signals |
| UNCLEAR | Insufficient Data |

## Acceptance criteria (all met)

- [x] `/api/signals/latest` returns regime label–derived signals when a persisted regime is available
- [x] Each signal has `asset_class`, `supporting_regime`, `supporting_drivers`, `conflicting_drivers`
- [x] `signal_direction` is separated from `signal_type` in the rule (not just a single string)
- [x] `signal_confidence` is a numeric score (not inferred from string strength alone)
- [x] Fallback to snapshot-based engine when no regime is available
- [x] Fallback sets `availability = "degraded"`, `degraded_reason = "regime_unavailable_fallback_engine_used"`
- [x] All 9 `RegimeLabel` values produce non-empty signal rules
- [x] Signal rationale is reusable by the explanation layer

## Tests

- `tests/unit/domain/signals/test_regime_signal_rules.py` — 14 tests
- `tests/unit/api/test_signals_router.py` — 13 tests (all existing pass)

## Remaining risks / follow-up

- Signal rules are deterministic; future Quant Scoring Engine should weight
  them dynamically based on indicator recency and conviction.
- `signal_confidence` is currently set per-rule in the map; should be derived
  from regime confidence level in a future iteration.
- Cross-asset signal conflicts (e.g. equities BUY vs bonds BUY in GOLDILOCKS)
  are not yet resolved by a conflict/consensus engine.
