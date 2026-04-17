# Snapshot Schema

Canonical models: `domain/macro/snapshot.py`

## MacroSnapshotState fields

- `snapshot_id`
- `as_of_date`
- `snapshot_timestamp`
- `freshness_status`
- `degraded_status`
- `growth_state`
- `inflation_state`
- `labor_state`
- `policy_state`
- `financial_conditions_state`
- `key_indicator_changes`
- `missing_indicators`
- `source_summary`
- `indicator_values`
- `comparison`

## Comparison metadata

- `baseline_available`
- `previous_snapshot_id`
- `changed_category_states`
- `changed_indicators`

## State vocabularies

- Growth: `accelerating | slowing | mixed | unknown`
- Inflation: `cooling | sticky | reaccelerating | unknown`
- Labor: `tight | softening | weak | unknown`
- Policy: `restrictive | neutral | easing_bias | unknown`
- Financial conditions: `tight | neutral | loose | unknown`
