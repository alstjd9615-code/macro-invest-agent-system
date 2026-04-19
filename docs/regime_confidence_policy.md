# Regime Confidence Policy

Canonical source: `domain/macro/regime_mapping.py`

Confidence values are deterministic and coarse-grained: `high | medium | low`.

## Confidence rules

### 1. Hard floor conditions — always `low`

- `degraded_status in {missing, source_unavailable}`, or
- `freshness_status in {stale, unknown}`, or
- mapped label is `mixed` or `unclear`.

### 2. Partial / late conditions — floor at `medium`

- `degraded_status = partial`, or
- `freshness_status = late`, or
- one category state is `unknown`.

### 3. Two or more unknown category states → `low`

### 4. `high` only when

- data is fresh and not degraded,
- category states are coherent (no unknown states),
- regime label is specific (not `mixed` / `unclear`).

## Quant score adjustment (added in Quant + Confidence PR)

When `QuantScoreBundle` is available and preliminary confidence is not
already `low`, two additional rules apply:

| Condition | Effect |
|---|---|
| `breadth < 0.60` (fewer than 3 of 5 dimensions known) | Cap at `medium`; cannot be `high` |
| `overall_support < 0.40` (weak quant backing) | Downgrade one level (high→medium or medium→low) |

Quant scores **never** raise confidence above its preliminary level.

**Note:** Quant scores are state-derived heuristics in v1.  They are not
statistically calibrated; future versions should apply proper calibration.
The current multipliers (`0.85×` for MEDIUM, `0.65×` for LOW) are
intentionally conservative to avoid overconfidence.

## Signal confidence derivation (Chunk 2 addition)

Signal scores (rule-level `signal_confidence`) are adjusted using the
regime's resolved confidence level:

| Regime confidence | Signal score multiplier |
|---|---|
| `high` | 1.00 (unchanged) |
| `medium` | 0.85 |
| `low` | 0.65 |

Additionally: if `QuantScoreBundle.overall_support < 0.35`, an additional
`0.85×` multiplier is applied.

## Missing input handling

- `missing_inputs` is propagated directly from snapshot `missing_indicators`.
- Regime builders do not impute missing indicator values.

## Confidence vs degraded vs mixed

These three concepts are orthogonal:

- **Confidence** (`high` / `medium` / `low`) — analytical certainty of the regime label.
- **Degraded** (`is_degraded=True`) — data/freshness/quality problem (input layer).
- **Mixed / conflict** (`is_mixed=True`) — analytical tension between macro drivers
  (interpretation layer).

A regime or signal can be high-confidence but have tension (e.g. goldilocks with
one restrictive policy driver).  A signal can be degraded AND conflicted at the same time.
