# Regime API Contract

Routes:

- `GET /api/regimes/latest`
- `GET /api/regimes/compare`
- `GET /api/regimes/history` *(added: History + Change Detection PR)*

Canonical files:

- router: `apps/api/routers/regimes.py`
- DTOs: `apps/api/dto/regimes.py`, `apps/api/dto/history.py`

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
- `current_rationale_summary`
- `warnings`, `is_seeded`
- `delta` — structured change object from Change Detection Engine v1 (see below)

### `delta` object (Change Detection Engine v1)

Present when `baseline_available=true`; `null` when no prior exists.

> **Note:** `severity` is explicitly **heuristic** (v1) — not statistically calibrated.
> See `severity_rationale` for the applied rule. Future PRs may refine calibration.

Fields:
- `is_initial` — true when no prior regime exists
- `label_changed`, `family_changed`, `confidence_changed`
- `confidence_direction` — `improved` | `weakened` | `unchanged` | `not_applicable`
- `severity` — `unchanged` | `minor` | `moderate` | `major` (heuristic v1)
- `changed_dimensions` — list: may include `"label"`, `"family"`, `"confidence"`
- `prior_label`, `prior_family`, `prior_confidence`
- `label_transition` — e.g. `"goldilocks → slowdown"`
- `confidence_transition` — e.g. `"high → medium"`
- `is_regime_transition` — true when label changed
- `notable_flags` — e.g. `["cross_family_transition"]`, `["high_severity_destination"]`
- `severity_rationale` — analyst-facing explanation of severity assignment

**Severity heuristic rules (v1):**

| Condition | Severity |
|---|---|
| No label or confidence change | `unchanged` |
| Label unchanged; confidence one level shift | `minor` |
| Label changed within same family; OR confidence skips two levels | `moderate` |
| Cross-family transition (family also changed) | `major` |
| Destination is `contraction` or `stagflation_risk` | `major` |

**Semantic distinctions:**
- `changed` ≠ `degraded` ≠ `mixed/conflicted`
- `changed` = time-based difference relative to a prior state
- `degraded` = data quality / freshness limitation
- `mixed/conflicted` = analytical tension in the current classification

Errors:
- `404` when no current regime exists on/before `as_of_date`

## `GET /api/regimes/history`

*(Added in History + Change Detection PR)*

Returns recent regime history for an as-of date, ordered most recent first.

Query params:
- `as_of_date` (optional, `YYYY-MM-DD`, defaults to today)
- `limit` (optional, integer 1–50, default 10)

Response fields:
- `as_of_date` — reference date the history was retrieved for
- `records` — ordered list of `HistoricalRegimeDTO` entries, most recent first
- `total` — number of records returned (≤ `limit_applied`)
- `limit_applied` — limit that was applied
- `latest_regime_id` — regime ID of the most recent record; `null` if empty
- `previous_regime_id` — regime ID of the second-most-recent; `null` if < 2 records

Each `HistoricalRegimeDTO` record carries:
- `regime_id`, `as_of_date`, `generated_at`
- `regime_label`, `regime_family`, `confidence`
- `freshness_status`, `degraded_status`
- `transition_type`, `transition_from_prior`, `changed`
- `warnings` — analyst-facing warnings at creation time
- `is_seeded`, `missing_inputs`, `supporting_snapshot_id`

Retrieval semantics:
- History includes all regimes stored on or before `as_of_date`, up to `limit`.
- Most-recent first ordering: ties broken by `regime_timestamp`.
- `latest_regime_id` / `previous_regime_id` identify the compare baseline pair.

Errors:
- `502` when the regime repository is not configured

