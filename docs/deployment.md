# Deployment Guide

This document covers how to deploy the `macro-invest-agent-platform` to a
local development environment or a staging/production-like setup, including
health checks, smoke validation, and rollback guidance.

---

## Local development

### Start all services

```bash
docker compose up -d
```

This brings up:
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | `5432` | Feature and signal persistence |
| MinIO | `9000` / `9001` | Raw data artefacts |
| Prometheus | `9090` | Metrics collection |
| Grafana | `3000` | Metrics dashboards |

Wait for all containers to be healthy:

```bash
docker compose ps
```

### Start the API

The FastAPI app is not yet containerised. Run it locally with:

```bash
uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run database migrations

```bash
alembic upgrade head
```

---

## Environment variables

All configuration is driven by environment variables. Copy the template and
fill in required values:

```bash
cp .env.example .env
```

### Required for production

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+psycopg://macro_user:macro_pass@localhost:5432/macro_db` |
| `FRED_API_KEY` | FRED API key (required for live data) | _(none)_ |
| `MINIO_ROOT_PASSWORD` | MinIO root password | `minioadmin` *(change in prod)* |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password | `admin` *(change in prod)* |

### Observability settings

| Variable | Description | Default |
|----------|-------------|---------|
| `METRICS_ENABLED` | Expose `/metrics` endpoint | `true` |
| `TRACING_ENABLED` | Export OTel traces | `false` |
| `OTLP_ENDPOINT` | OTLP HTTP endpoint | `http://localhost:4318` |
| `OTEL_SERVICE_NAME` | OTel service name | `macro-invest-agent-platform` |
| `OTEL_SAMPLE_RATE` | Trace sample rate (0–1) | `1.0` |

### Safe defaults

- `METRICS_ENABLED=true` is safe; it only exposes counters and histograms
  with no sensitive data.
- `TRACING_ENABLED=false` by default — enable only when a trace backend is
  available.
- Never commit a real `FRED_API_KEY` to source control.

---

## Health and readiness probes

The API exposes two lightweight probe endpoints:

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /health` | Liveness — process alive? | `{"status": "ok"}` |
| `GET /readiness` | Readiness — config valid? | `{"status": "ready", "env": "..."}` |
| `GET /metrics` | Prometheus scrape | Prometheus text format |

Use `/health` for Kubernetes **liveness** probes and `/readiness` for
**readiness** probes.

### Kubernetes example

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /readiness
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
```

---

## Post-deploy smoke checks

Run these checks after every deploy to confirm the system is healthy.

### 1. API liveness

```bash
curl -s http://localhost:8000/health
# Expected: {"status":"ok"}
```

### 2. API readiness

```bash
curl -s http://localhost:8000/readiness
# Expected: {"status":"ready","env":"local"}
```

### 3. Metrics endpoint

```bash
curl -s http://localhost:8000/metrics | grep macro_platform | head -10
# Expected: Prometheus text lines starting with # HELP / # TYPE
```

### 4. Prometheus scrape target

Open http://localhost:9090/targets and confirm the `macro-platform` job shows
**UP**.

### 5. Grafana dashboard

Open http://localhost:3000 (admin / admin) → Dashboards →
**Macro Platform — Runtime Overview**.  Confirm panels load without errors.

### 6. Unit tests

```bash
uv run pytest --cov=. -q
# All tests should pass
```

---

## Rollback guidance

### Docker Compose rollback

If a deployment introduces a regression:

1. **Identify the previous working image tag** from your container registry
   or git history.

2. **Update the image tag** in `docker-compose.yml` (or set an
   `API_IMAGE_TAG` environment variable if parameterised).

3. **Redeploy:**
   ```bash
   docker compose pull api
   docker compose up -d api
   ```

4. **Run smoke checks** (see above) to confirm the rollback is successful.

### Git-based rollback

```bash
# Find the last known-good commit
git log --oneline -20

# Check out the tag or commit
git checkout v0.1.2   # or a specific SHA

# Rebuild and redeploy
docker compose build api
docker compose up -d api
```

### Database rollback (Alembic)

If the deploy included a database migration:

```bash
# Roll back one migration step
alembic downgrade -1

# Or roll back to a specific revision
alembic downgrade <revision_id>
```

⚠️ Database rollbacks may cause data loss if the migration added columns with
data.  Review the migration file before running a downgrade.

---

## Observability stack setup

### Grafana access

After `docker compose up -d`:

```
URL:      http://localhost:3000
Username: admin
Password: admin  (change via GRAFANA_ADMIN_PASSWORD)
```

The **Macro Platform — Runtime Overview** dashboard is auto-provisioned.
Import additional dashboards from `docs/dashboards/` via Grafana's
**Dashboards → Import** UI.

### Prometheus alert rules

Alert rules are loaded from `docs/alerts/prometheus_rules.yml` via the
Prometheus volume mount in `docker-compose.yml`.  After editing rules:

```bash
# Reload Prometheus configuration without restart
curl -X POST http://localhost:9090/-/reload
```

### Connecting Jaeger / Tempo for traces

```bash
# Start Jaeger all-in-one
docker run -d --name jaeger \
  --network macro-invest-agent-system_default \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Enable tracing in .env
TRACING_ENABLED=true
OTLP_ENDPOINT=http://localhost:4318
```

Restart the API and open http://localhost:16686 to view traces.

---

## Security notes

- The `/metrics` endpoint contains only counters and histograms — no PII,
  no API keys, no user data.
- Never expose PostgreSQL, MinIO, or Prometheus ports directly to the public
  internet.  Place them behind a VPC or internal load balancer.
- Rotate `GRAFANA_ADMIN_PASSWORD` and `MINIO_ROOT_PASSWORD` before promoting
  to a shared staging environment.
- The FRED API key is stored as a `SecretStr` in settings and is never logged
  or emitted as a span attribute.
