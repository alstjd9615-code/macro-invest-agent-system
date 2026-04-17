# Runbooks

Concise operational guides for the `macro-invest-agent-platform`.

| Runbook | Triggered by |
|---------|-------------|
| [Pipeline Stuck or Failing](pipeline_stuck_or_failing.md) | `PipelineConsecutiveFailures`, `PipelineSlowRuns`, `AgentHighErrorRate` |
| [Provider Data Unavailable](provider_data_unavailable.md) | `ProviderHighErrorRate`, `ProviderSlowFetches`, `MCPToolHighErrorRate` |
| [Stale Feature Store Data](stale_feature_store_data.md) | Manual inspection, `PipelineConsecutiveFailures` |
| [Trace/Metric Visibility Gap](visibility_gap.md) | `MetricsEndpointDown`, missing traces in Jaeger/Tempo |
| [Schema Regression After Deploy](schema_regression_after_deploy.md) | `SchemaValidationFailures` |

## How to use these runbooks

1. An alert fires.  Open the runbook linked in the alert's `runbook` annotation.
2. Follow the **Immediate triage** steps first — most incidents can be
   categorised within 2–3 minutes.
3. Apply the **Mitigation** steps.
4. If the issue is not resolved, escalate using the **Escalation path**.
5. After resolution, note the cause and update the runbook if the steps were
   incomplete.
