# Regime API Contract

Routes:

- `GET /api/regimes/latest`
- `GET /api/regimes/compare`

Canonical files:

- router: `apps/api/routers/regimes.py`
- DTOs: `apps/api/dto/regimes.py`

## `GET /api/regimes/latest`

Query params:
- `as_of_date` (optional, `YYYY-MM-DD`, defaults to today)

Response fields:
- `as_of_date`, `regime_id`, `regime_timestamp`
- `regime_label`, `regime_family`, `confidence`
- `freshness_status`, `degraded_status`, `missing_inputs`
- `supporting_snapshot_id`, `supporting_states`
- `transition` (`transition_from_prior`, `transition_type`, `changed`)
- `rationale_summary`

Errors:
- `404` when no persisted regime exists

## `GET /api/regimes/compare`

Query params:
- `as_of_date` (optional, `YYYY-MM-DD`, defaults to today)

Response fields:
- `as_of_date`
- `baseline_available`
- `current_regime_label`, `prior_regime_label`
- `transition_type`, `changed`
- `current_confidence`, `prior_confidence`

Errors:
- `404` when no current regime exists on/before `as_of_date`
