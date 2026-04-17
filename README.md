# macro-invest-agent-platform

Macroeconomic data ingestion and analysis platform for deterministic investment research workflows.

## Why this exists

- Build a reliable macro data foundation (ingestion, normalization, freshness).
- Keep deterministic domain outputs as the source of truth.
- Separate data/logic layers from agent-facing interfaces.

## Current status

- **Phase 1 (Macro Data Foundation): in progress**
- Priority ingestion foundation implemented for CPI, Unemployment, 10Y Yield, PMI, Retail Sales.

## Local run (quickstart)

1. Install dependencies:

```bash
uv sync --all-extras
```

2. Start local services:

```bash
docker compose up -d
```

3. Key endpoints:

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health
- Frontend: http://localhost:8080
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## High-level components

- **Domain/Core**: deterministic macro + signal models and rules.
- **Pipelines**: macro ingestion and normalization workflows.
- **API**: analyst-facing read API.
- **Observability**: Prometheus metrics + Grafana dashboards.

## Canonical documentation

- Architecture: `docs/architecture.md`
- Roadmap/Phases: `docs/roadmap.md`
- Macro indicator catalog: `docs/macro_indicator_catalog.md`
- Ingestion behavior/flow: `docs/ingestion_design.md`
- Storage schema/rules: `docs/storage_schema.md`
- Freshness policy: `docs/freshness_policy.md`
- Metrics reference: `docs/metrics.md`
- Deployment: `docs/deployment.md`
