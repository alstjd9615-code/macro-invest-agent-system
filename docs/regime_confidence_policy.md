# Regime Confidence Policy

Canonical source: `domain/macro/regime_mapping.py`

Phase 3 confidence values are deterministic and coarse-grained:
`high | medium | low`.

## Confidence rules

1. `low` when:
   - `degraded_status in {missing, source_unavailable}`, or
   - `freshness_status in {stale, unknown}`, or
   - mapped label is `mixed` or `unclear`.
2. `medium` when:
   - `degraded_status = partial`, or
   - `freshness_status = late`, or
   - one category state is `unknown`.
3. `high` only when:
   - data is fresh and not degraded,
   - category states are coherent (no unknown states),
   - and regime label is specific (not `mixed` / `unclear`).

## Missing input handling

- `missing_inputs` is propagated directly from snapshot `missing_indicators`.
- Regime builders should not invent or impute missing indicator values in Phase 3.
