# Regime Schema

Canonical models: `domain/macro/regime.py`

## MacroRegime fields

- `regime_id`
- `as_of_date`
- `regime_timestamp`
- `regime_label`
- `regime_family`
- `supporting_snapshot_id`
- `supporting_states`
- `confidence`
- `freshness_status`
- `degraded_status`
- `missing_inputs`
- `transition`
- `rationale_summary`

## Regime vocabulary

- `goldilocks`
- `disinflation`
- `slowdown`
- `reflation`
- `stagflation_risk`
- `contraction`
- `policy_tightening_drag`
- `mixed`
- `unclear`

## Confidence vocabulary

- `high`
- `medium`
- `low`

## Transition metadata

`RegimeTransition` fields:

- `transition_from_prior`
- `transition_type`: `initial | unchanged | shift | weakening | strengthening | unknown`
- `changed`
