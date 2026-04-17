# Runbook: Provider Data Unavailable

**Alerts:** `ProviderHighErrorRate`, `ProviderSlowFetches`, `MCPToolHighErrorRate`

---

## Symptoms

- `macro_platform_provider_fetch_total{result="failure"}` is elevated for a
  specific provider (e.g. `fred`).
- `macro_platform_provider_fetch_duration_seconds` p95 is near or above the
  configured timeout (default 10 s).
- Agent operations return errors or degraded responses referencing a provider
  failure.

---

## Immediate triage

1. **Identify the failing provider:**
   ```promql
   sum by (provider) (rate(macro_platform_provider_fetch_total{result="failure"}[5m]))
   ```

2. **Check the error type in logs:**
   ```bash
   docker compose logs api | jq 'select(.event == "fred_fetch_failed")'
   ```
   The `error` field distinguishes:
   - `"http_error"` with `http_status` → provider API responded with a non-200
     status.
   - `"timeout"` → request exceeded the configured `FRED_REQUEST_TIMEOUT_S`.
   - `"network_error"` → OS-level connection failure.

3. **Test provider reachability:**
   ```bash
   curl -s "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&api_key=<key>&limit=1&file_type=json" | python3 -m json.tool
   ```
   Replace `<key>` with the value from your `.env`.  A `200` response confirms
   the provider is reachable.

4. **Check provider status page:**
   - FRED: https://fred.stlouisfed.org/

---

## Mitigation

### `http_status: 429` — rate limited
- FRED free tier allows up to 120 requests per minute.
- Reduce the number of indicators fetched per run, or space out pipeline
  invocations.
- Consider caching fetch results for indicators that change infrequently.

### `http_status: 401` / `403` — invalid API key
- Verify `FRED_API_KEY` in `.env` is correct and not expired.
- Rotate the key in the FRED developer dashboard if necessary.
- Update the secret and restart the application:
  ```bash
  docker compose restart api
  ```

### Timeout / network error
- Increase `FRED_REQUEST_TIMEOUT_S` in `.env` (e.g. from `10.0` to `20.0`)
  if the provider is simply slow.
- Check DNS and firewall rules from the host running the application.
- If the provider is fully unreachable, fall back to fixture data for
  development use (set `source=fixture` in the pipeline configuration).

### Provider outage
- Monitor the provider status page.
- Set the pipeline to use the fixture source until the provider recovers.
- Communicate expected data freshness degradation to users.

---

## Post-mitigation checks

```promql
# Confirm provider fetch success rate recovering
sum by (provider) (rate(macro_platform_provider_fetch_total{result="success"}[5m]))
```

```promql
# Confirm latency is back below timeout threshold
histogram_quantile(0.95, sum by (provider, le) (rate(macro_platform_provider_fetch_duration_seconds_bucket[5m])))
```

---

## Escalation path

If provider errors persist beyond 1 hour:
1. File an issue with the provider (e.g. FRED support for extended outage).
2. Enable the fixture source as a temporary fallback.
3. Notify analysts that data may be stale until the provider recovers.
