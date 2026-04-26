# Backlog: 0403 — Quant Scoring Engine v1 + Confidence Refactor + Conflict Surface v1

**Priority:** P0  
**Workstream:** Multi-Engine Analysis Hub — Quant + Confidence + Conflict bridge  
**Status:** ✅ Implemented

---

## Scope

Three sequential, coherent chunks forming a single logical PR:

1. **Chunk 1 — Quant Scoring Engine v1**: Introduce the first explicit
   quantitative scoring layer beneath regime and signal interpretation.
2. **Chunk 2 — Confidence Refactor**: Refactor regime and signal confidence
   so it is informed by quant scores plus quality/freshness context.
3. **Chunk 3 — Conflict Surface v1**: Introduce lightweight but explicit
   conflict/mixed-signal semantics for product surfaces.

---

## Chunk 1 — Quant Scoring Engine v1

### Files changed

| File | Change |
|---|---|
| `domain/quant/__init__.py` | New package |
| `domain/quant/models.py` | New: `ScoreDimension`, `ScoreLevel`, `DimensionScore`, `QuantScoreBundle` |
| `domain/quant/scoring.py` | New: per-dimension scoring functions + `score_snapshot()` entry point |
| `services/quant_scoring_service.py` | New: `QuantScoringService.compute()` wrapper |
| `tests/unit/domain/quant/test_scoring.py` | 33 new tests |

### Score dimensions

| Dimension | Score 1.0 state | Score 0.0 state |
|---|---|---|
| growth | accelerating | slowing |
| inflation | cooling | reaccelerating |
| labor | tight | weak |
| policy | easing_bias | restrictive |
| financial_conditions | loose | tight |

### Secondary measures

- `breadth` — fraction of dimensions with known scores [0.0, 1.0]
- `momentum` — proportion of strong/moderate dimension scores [0.0, 1.0]
- `change_intensity` — score dispersion as proxy for rate-of-change [0.0, 1.0]
- `overall_support` — breadth-weighted mean of known dimension scores [0.0, 1.0]

### What Chunk 2 can rely on

- `QuantScoreBundle.overall_support` — overall quant backing [0.0, 1.0]
- `QuantScoreBundle.breadth` — data coverage fraction [0.0, 1.0]
- All values deterministic and testable given the same snapshot input.

---

## Chunk 2 — Confidence Refactor

### Files changed

| File | Change |
|---|---|
| `domain/macro/regime.py` | Added `quant_scores: QuantScoreBundle | None` field to `MacroRegime` |
| `domain/macro/regime_mapping.py` | Added `quant_scores` parameter to `derive_regime_confidence()`; added import |
| `services/macro_regime_service.py` | Added `score_snapshot()` call; passes `quant_scores` into `derive_regime_confidence()` and `MacroRegime` |
| `services/signal_service.py` | Added `_adjust_signal_score()` helper; applies regime-confidence multipliers to signal scores |
| `tests/unit/domain/macro/test_quant_confidence.py` | 22 new tests |

### Confidence adjustment rules (Chunk 2 additions)

Applied only when `quant_scores` is provided and preliminary confidence is not already LOW:

- `breadth < 0.60` → cap at MEDIUM (insufficient dimension coverage)
- `overall_support < 0.40` → downgrade one level (HIGH→MEDIUM or MEDIUM→LOW)

### Signal score adjustment

| Regime confidence | Score multiplier |
|---|---|
| HIGH | 1.00 (unchanged) |
| MEDIUM | 0.85 |
| LOW | 0.65 |

Additional 0.85× if `quant_overall_support < 0.35`.

### What Chunk 3 can rely on

- `MacroRegime.quant_scores` — populated by `MacroRegimeService.build_regime()`
- `MacroRegime.confidence` — now informed by quant scores
- Signal scores are adjusted downward for low-confidence/low-quant regimes.

---

## Chunk 3 — Conflict Surface v1

### Files changed

| File | Change |
|---|---|
| `domain/signals/conflict.py` | New: `ConflictStatus`, `ConflictSurface`, `derive_conflict()` |
| `domain/signals/models.py` | Added `conflict: ConflictSurface | None` to `SignalOutput` |
| `apps/api/dto/signals.py` | Added `conflict_status`, `is_mixed`, `conflict_note`, `quant_support_level` to `SignalSummaryDTO` |
| `apps/api/dto/builders.py` | Updated `signal_output_to_dto()` to map conflict fields |
| `services/signal_service.py` | Added `derive_conflict()` call in `run_regime_grounded_engine()` |
| `tests/unit/domain/signals/test_conflict.py` | 33 new tests |

### Conflict status vocabulary

| Status | Meaning |
|---|---|
| `clean` | All drivers support the signal coherently |
| `tension` | ≥1 conflicting driver but supporting > conflicting |
| `mixed` | Conflicting ≥ supporting (roughly balanced) |
| `low_conviction` | No supporting drivers, or quant very weak (<0.35) |

### Degraded vs Mixed — explicit distinction

- **Degraded** (`is_degraded=True`) = data/quality/freshness problem (input layer)
- **Mixed/conflict** (`is_mixed=True`) = analytical tension between drivers (interpretation layer)

These are orthogonal. A signal can be both degraded AND conflicted.

---

## Tests added

| File | Tests |
|---|---|
| `tests/unit/domain/quant/test_scoring.py` | 33 |
| `tests/unit/domain/macro/test_quant_confidence.py` | 22 |
| `tests/unit/domain/signals/test_conflict.py` | 33 |
| **Total new** | **88** |
| Baseline | 787 |
| **Final** | **875** |

---

## Known limitations / deferred work

- Quant scores are state-derived (not time-series calibrated). True
  momentum/change-intensity requires consecutive snapshot comparison.
- `signal_confidence` multipliers are heuristic, not statistically calibrated.
- Conflict engine v1 only uses driver counts; a future ensemble engine should
  use weighted cross-asset conflict resolution.
- No LLM-backed explanation generation in this PR.
- Portfolio/scenario layers remain deferred.
- Explanation layer not yet updated to surface quant scores or conflict notes.
