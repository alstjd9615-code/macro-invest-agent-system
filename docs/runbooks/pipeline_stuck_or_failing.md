# Runbook: Pipeline Stuck or Failing

**Alerts:** `PipelineConsecutiveFailures`, `PipelineSlowRuns`

---

## Symptoms

- `macro_platform_pipeline_runs_total{result="failure"}` is increasing.
- Feature store data timestamps are falling behind (data freshness degraded).
- Agent responses may return stale or partial data warnings.

---

## Immediate triage

1. **Check pipeline failure count and source:**
   ```promql
   increase(macro_platform_pipeline_runs_total{result="failure"}[30m])
   ```
   Note the `source` label — it identifies which data source is failing.

2. **Check provider error rate for that source:**
   ```promql
   sum by (provider) (rate(macro_platform_provider_fetch_total{result="failure"}[5m]))
   ```
   If the provider error rate is high, see
   [provider_data_unavailable.md](provider_data_unavailable.md).

3. **Check application logs** for the ingestion service:
   ```bash
   docker compose logs api | grep "ingestion_provider_error\|RuntimeError"
   # or, with JSON logs:
   docker compose logs api | jq 'select(.event | startswith("ingestion"))'
   ```
   Look for `failure_category` (e.g. `PROVIDER_TIMEOUT`, `PROVIDER_HTTP_ERROR`).

4. **Check infrastructure health:**
   ```bash
   docker compose ps
   ```
   Confirm PostgreSQL and MinIO containers are healthy.

---

## Mitigation

### Transient provider error
- Wait for the next scheduled pipeline run.  Most provider errors self-resolve.
- If the error is a rate-limit (`429`), increase the retry backoff or reduce
  fetch frequency.

### Persistent provider outage
- Disable the failing source in the source registry until the provider
  recovers.
- Switch to a fallback or fixture source for development/staging.

### Infrastructure issue (Postgres/MinIO down)
```bash
docker compose restart postgres minio
docker compose ps  # wait for healthy
```
Then re-trigger the pipeline manually:
```bash
uv run python -m pipelines.ingestion.macro_ingest --country US
```

### Pipeline process hung
```bash
# Find the PID and restart the application
docker compose restart api
```

---

## Post-mitigation checks

```promql
# Confirm pipeline success rate recovering
sum by (source) (rate(macro_platform_pipeline_runs_total{result="success"}[10m]))
```

Check that feature store snapshots have a recent `ingested_at` timestamp.

---

## Escalation path

If the pipeline has not recovered within 30 minutes of mitigation:
1. Check for upstream provider announcements (FRED status page, etc.).
2. Consider switching to the fixture source for analyst workflows while the
   real source is unavailable.
3. Engage the on-call engineer if data freshness SLA is at risk.
