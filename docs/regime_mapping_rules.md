# Regime Mapping Rules

Canonical source: `domain/macro/regime_mapping.py`

Phase 3 mapping is deterministic and ordered. The first matching rule wins.

## Input states

- `growth_state`
- `inflation_state`
- `labor_state`
- `policy_state`
- `financial_conditions_state`
- `freshness_status`
- `degraded_status`

## Gate rules (applied first)

1. `degraded_status in {missing, source_unavailable}` -> `unclear`
2. `freshness_status in {stale, unknown}` -> `unclear`
3. any category state is `unknown` -> `mixed`

## Label rules

1. **goldilocks**: growth accelerating + inflation cooling + labor tight/softening + policy neutral/easing_bias + financial conditions neutral/loose
2. **disinflation**: inflation cooling + growth mixed/slowing
3. **slowdown**: growth slowing + labor softening/weak + inflation sticky/cooling
4. **reflation**: inflation reaccelerating + growth accelerating/mixed + policy easing_bias
5. **stagflation_risk**: growth slowing + inflation reaccelerating + labor softening/weak
6. **contraction**: growth slowing + labor weak + policy restrictive + financial conditions tight
7. **policy_tightening_drag**: policy restrictive + financial conditions tight + growth slowing/mixed
8. fallback -> `mixed`

## Output contract

- label: `RegimeLabel`
- family: derived via canonical mapping (`docs/regime_vocabulary.md`)
- rationale summary: deterministic state string
