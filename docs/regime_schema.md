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

Vocabulary and label-family mapping are defined in:

- `docs/regime_vocabulary.md`

## Transition metadata

`RegimeTransition` fields:

- `transition_from_prior`
- `transition_type`: `initial | unchanged | shift | weakening | strengthening | unknown`
- `changed`
