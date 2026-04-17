# Runbook: Stale Feature Store Data

**Triggers:** `PipelineConsecutiveFailures` (sustained), manual freshness check

---

## Symptoms

- The ingestion pipeline has not produced a successful snapshot in longer than
  expected (e.g. > 24 hours for daily data).
- Agent responses reference feature timestamps that are more than one
  scheduled-run interval old.
- `StaleDataError` appears in application logs.

---

## Immediate triage

1. **Check pipeline success recency:**
   ```promql
   # Time since last successful pipeline run (approximate, per source)
   time() - max by (source) (
     macro_platform_pipeline_runs_total{result="success"} * on() group_left()
     max_over_time(timestamp(macro_platform_pipeline_runs_total{result="success"})[1h:5m])
   )
   ```
   A simpler approach: check the `ingested_at` field of the latest snapshot
   directly in the database:
   ```sql
   SELECT source_id, MAX(ingested_at) AS latest_ingest
   FROM feature_snapshots
   GROUP BY source_id;
   ```

2. **Check pipeline failure logs:**
   ```bash
   docker compose logs api | jq 'select(.event | contains("ingestion"))'
   ```

3. **Confirm the pipeline is scheduled and running:**
   Depending on your scheduler (cron, Prefect, etc.), verify that pipeline
   runs are being triggered on schedule.

---

## Mitigation

### Force a manual pipeline run
```bash
uv run python -m pipelines.ingestion.macro_ingest --country US --source fred
```

Verify the run succeeded:
```bash
docker compose logs api | jq 'select(.event == "ingestion_complete")'
```

### Pipeline blocked by provider outage
Follow [provider_data_unavailable.md](provider_data_unavailable.md) first,
then re-trigger the pipeline manually after the provider recovers.

### Scheduler not running
If using a cron-based schedule:
```bash
crontab -l  # confirm the job is present
# Re-register if missing
```
If using Prefect or another orchestrator, check the orchestrator UI for failed
or stuck flow runs.

---

## Post-mitigation checks

Confirm a new snapshot exists with a recent `ingested_at`:
```sql
SELECT source_id, MAX(ingested_at) FROM feature_snapshots GROUP BY source_id;
```

Confirm agent responses no longer reference stale timestamps.

---

## Escalation path

If stale data persists beyond 2 scheduled run intervals:
1. Notify analysts that features are stale and investment signals should not
   be acted upon.
2. Engage the platform team to diagnose the scheduler or provider issue.
