# Runbook: Trace/Metric Visibility Gap

**Alert:** `MetricsEndpointDown`, missing traces in Jaeger / Grafana Tempo

---

## Symptoms

- The `MetricsEndpointDown` alert fires: no `macro_platform_*` metrics have
  been scraped for 5+ minutes.
- Grafana dashboards show "No data" for all panels.
- Jaeger / Tempo shows no recent traces for `macro-invest-agent-platform`.
- Prometheus target page shows the scrape job in DOWN state.

---

## Immediate triage

### Check whether the application process is running

```bash
docker compose ps
# Expect: api   running (healthy)
```

If the `api` container is stopped or restarting:
```bash
docker compose logs api --tail=50
```
Look for Python exceptions, `OOMKilled` messages, or startup errors.

### Check the /metrics endpoint directly

```bash
curl -s http://localhost:8000/metrics | head -20
```

Expected: Prometheus text-format output beginning with `# HELP ...`.

If the endpoint returns a connection error, the application is down.
If it returns `200` with no metrics, `METRICS_ENABLED` may be set to `false`.

### Check Prometheus scrape status

Open the Prometheus UI → **Status → Targets** (`http://localhost:9090/targets`)
and check whether the `macro-platform` job is listed as UP or DOWN.

If the target shows a scrape error, verify the `scrape_configs` in
`deploy/prometheus.yml` point to the correct host and port.

### Check tracing separately

If only traces are missing (metrics are fine):
```bash
# Confirm the OTLP endpoint is reachable
curl -s http://localhost:4318/
# Confirm tracing is enabled in settings
grep TRACING_ENABLED .env
```

If `TRACING_ENABLED=false`, traces are disabled by design.
If the Jaeger/Tempo container is down:
```bash
docker compose logs jaeger  # or tempo
docker compose restart jaeger
```

---

## Mitigation

### Application process is down
```bash
docker compose restart api
# Wait for healthy
docker compose ps
curl http://localhost:8000/health
```

### Metrics disabled
If `METRICS_ENABLED=false` is set intentionally (e.g. during a maintenance
window), re-enable it and restart:
```bash
# Edit .env: METRICS_ENABLED=true
docker compose restart api
```

### Prometheus cannot reach the scrape target
- Confirm the `api` container is on the same Docker network as Prometheus.
- Update `deploy/prometheus.yml` `targets` if the API port changed.
- Reload Prometheus configuration:
  ```bash
  curl -X POST http://localhost:9090/-/reload
  ```

---

## Post-mitigation checks

```bash
# Metrics scraping
curl -s http://localhost:8000/metrics | grep macro_platform | head -5

# Prometheus target UP
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "macro-platform") | .health'
```

---

## Escalation path

If the application cannot start after a restart:
1. Check for recent code changes that may have introduced an import error.
2. Roll back to the previous container image tag.
3. File an incident if visibility is still degraded > 15 minutes.
