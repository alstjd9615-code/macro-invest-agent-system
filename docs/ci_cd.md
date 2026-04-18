# CI/CD Quick Guide

This repository uses GitHub Actions for CI only.
**CD is disabled** — the project is currently deployed manually via Docker Compose.

---

## CI pipeline

Workflow: `.github/workflows/ci.yml`

Triggers:
- `pull_request`
- `push` (all branches)

Jobs (run in parallel):

| Job | Command | Purpose |
|-----|---------|---------|
| **lint** | `uv run ruff check .` | Ruff lint check |
| **typecheck** | `uv run mypy .` | Mypy strict type check |
| **tests** | `uv run pytest tests --cov` | pytest + coverage |
| **docker-build** | `docker build -f ...` | Verify both Docker images build |

No secrets are required for CI.

---

## CD status: disabled

The CD workflow (`.github/workflows/cd.yml`) is **disabled**.  
No remote deployment is configured.

All deployments are performed manually — see the local workflow below.

---

## Local deployment workflow

### 1. Pull latest code

```bash
git pull origin main
```

### 2. Rebuild and start all services

```bash
docker compose up -d --build
```

This builds and starts:

| Service | Port | Purpose |
|---------|------|---------|
| `api` | `8000` | FastAPI backend |
| `frontend` | `8080` | Analyst dashboard |
| `postgres` | `5432` | Feature/signal persistence |
| `minio` | `9000` / `9001` | Object store |
| `prometheus` | `9090` | Metrics |
| `grafana` | `3000` | Dashboards |

### 3. Verify containers are running

```bash
docker compose ps
```

All containers should show `healthy` or `running`.

### 4. Smoke checks

```bash
# API liveness
curl -s http://localhost:8000/health
# Expected: {"status":"ok"}

# API readiness
curl -s http://localhost:8000/readiness
# Expected: {"status":"ready","env":"local"}

# Dashboard
open http://localhost:8080
```

### 5. View logs

```bash
docker compose logs -f api
docker compose logs -f frontend
```

### 6. Stop all services

```bash
docker compose down
```

---

## Running CI checks locally

```bash
# Lint
uv run ruff check .

# Type check
uv run mypy .

# Tests with coverage
uv run pytest tests --cov --cov-report=term-missing -q
```

---

## Required environment variables

Copy the template and fill in values:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | DB username | `macro_user` |
| `POSTGRES_PASSWORD` | DB password | `macro_pass` |
| `POSTGRES_DB` | Database name | `macro_db` |
| `MINIO_ROOT_USER` | MinIO admin user | `minioadmin` |
| `MINIO_ROOT_PASSWORD` | MinIO admin password | `minioadmin` |
| `FRED_API_KEY` | FRED API key (for live data) | _(empty, uses synthetic data)_ |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password | `admin` |
