# Metrics Reference

This document describes every Prometheus metric exposed by the
`macro-invest-agent-platform`, the question each metric answers, its labels,
and guidance on safe alert thresholds.

Metrics are exposed at `GET /metrics` (Prometheus text format) by the FastAPI
application and scraped by Prometheus.  Enable or disable the endpoint with
`METRICS_ENABLED=true|false` (default: `true`).

---

## Naming conventions

All metrics use the prefix `macro_platform_`.  Names follow the pattern:

```
macro_platform_<subsystem>_<name>_<unit>
```

Units are expressed as suffixes: `_total` (counter), `_seconds` (duration),
`_ratio` (0–1 gauge).

---

## Agent runtime metrics

### `macro_platform_agent_requests_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `operation` (`review_signals` \| `summarize_macro_snapshot` \| `compare_snapshots`), `result` (`success` \| `failure`) |
| Answers | How many agent requests are being served, and what fraction fail? |

**Operational use:** Use the `result="failure"` time series to page on sustained
agent errors.  Compare across operations to spot regressions after deploys.

---

### `macro_platform_agent_request_duration_seconds`

| Property | Value |
|---|---|
| Type | Histogram |
| Labels | `operation` |
| Buckets | 50 ms, 100 ms, 250 ms, 500 ms, 1 s, 2.5 s, 5 s, 10 s, 30 s |
| Answers | How long does each agent operation take end-to-end? |

**Operational use:** Alert on p99 > 10 s.  Correlate latency increases with
provider fetch latency (`macro_platform_provider_fetch_duration_seconds`) to
isolate the root cause.

---

### `macro_platform_schema_validation_failures_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `response_type` (`SignalReviewResponse` \| `MacroSnapshotSummaryResponse` \| `SnapshotComparisonResponse`) |
| Answers | Are agent output schemas regressing after a deploy? |

**Operational use:** This counter should be zero in normal operation.  Any
non-zero value after a deploy is a signal that a schema or formatter changed
incompatibly.  See [runbook: schema regression after deploy](runbooks/schema_regression_after_deploy.md).

---

### `macro_platform_degraded_responses_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `operation` |
| Answers | How often is the system returning partial or stale data to callers? |

**Operational use:** A sustained rate (> 5 % of requests over 15 minutes)
indicates upstream data quality issues.  Correlate with
`macro_platform_provider_fetch_total{result="failure"}` to identify the
affected provider.

---

## MCP tool metrics

### `macro_platform_mcp_tool_calls_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `tool` (`get_macro_snapshot` \| `run_signal_engine`), `result` (`success` \| `failure`) |
| Answers | Which MCP tools are failing, and at what rate? |

---

### `macro_platform_mcp_tool_duration_seconds`

| Property | Value |
|---|---|
| Type | Histogram |
| Labels | `tool` |
| Buckets | 10 ms, 50 ms, 100 ms, 250 ms, 500 ms, 1 s, 2.5 s, 5 s |
| Answers | How long does each MCP tool take to respond? |

---

## Provider fetch metrics

### `macro_platform_provider_fetch_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `provider` (e.g. `fred`), `result` (`success` \| `failure`) |
| Answers | Is a data provider repeatedly timing out or returning errors? |

**Operational use:** Alert when the failure rate for a provider exceeds 20 % over
5 minutes.  See [runbook: provider data unavailable](runbooks/provider_data_unavailable.md).

---

### `macro_platform_provider_fetch_duration_seconds`

| Property | Value |
|---|---|
| Type | Histogram |
| Labels | `provider` |
| Buckets | 100 ms, 250 ms, 500 ms, 1 s, 2.5 s, 5 s, 10 s, 30 s |
| Answers | Is a provider getting slower over time? |

---

## Signal generation metrics

### `macro_platform_signal_generation_duration_seconds`

| Property | Value |
|---|---|
| Type | Histogram |
| Labels | _(none)_ |
| Buckets | 1 ms, 5 ms, 10 ms, 50 ms, 100 ms, 250 ms, 500 ms, 1 s |
| Answers | Is the deterministic signal engine still fast, or has something regressed? |

**Operational use:** The signal engine is pure-CPU and should be fast (< 50 ms
for typical inputs).  A sustained p99 > 500 ms suggests a loop performance
regression or unexpectedly large signal definitions.

---

## Ingestion pipeline metrics

### `macro_platform_pipeline_runs_total`

| Property | Value |
|---|---|
| Type | Counter |
| Labels | `source` (e.g. `fred`, `fixture`), `result` (`success` \| `failure`) |
| Answers | Is the ingestion pipeline completing successfully? |

**Operational use:** Alert when the failure rate for any source exceeds 3
consecutive failures.  See [runbook: pipeline stuck or failing](runbooks/pipeline_stuck_or_failing.md).

---

### `macro_platform_pipeline_run_duration_seconds`

| Property | Value |
|---|---|
| Type | Histogram |
| Labels | `source` |
| Buckets | 0.5 s, 1 s, 2.5 s, 5 s, 10 s, 30 s, 60 s, 120 s |
| Answers | Is the pipeline taking longer than expected? |

---

## Label cardinality

All labels use bounded enumerable values.  The following labels are **never**
used:
- Per-request identifiers (`request_id`, `trace_id`)
- Country codes or indicator names (unbounded in theory)
- Free-form error messages

This keeps total time series count well under 100 for a single-instance
deployment, safe for any Prometheus setup.

---

## Adding new metrics

Follow these rules when adding metrics:

1. Define the metric object in `core/metrics/registry.py` with a docstring.
2. Export it from `core/metrics/__init__.py`.
3. Keep label values bounded (< 20 distinct values per label).
4. Record observations at the **boundary** of the operation — not inside loops.
5. Update this document with the new metric entry.
6. Pair every new counter with at least one alert rule in
   `docs/alerts/prometheus_rules.yml`.
