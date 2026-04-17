# macro-invest-agent-platform

Macroeconomic data ingestion and analysis platform for deterministic investment research workflows.

## Why this exists

- Build a reliable macro data foundation (ingestion, normalization, freshness).
- Keep deterministic domain outputs as the source of truth.
- Separate data/logic layers from agent-facing interfaces.

## Current status

- **Phase 1 (Macro Data Foundation): baseline complete**
- **Phase 2 (Macro Snapshot Layer): baseline complete**
- **Phase 3 (Macro Regime Engine): in progress**

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
- **Snapshot layer**: deterministic macro state structuring and comparison.
- **Regime layer**: deterministic snapshot-to-regime contract and classification.
- **API**: analyst-facing read API.
- **Observability**: Prometheus metrics + Grafana dashboards.

## Canonical documentation

- Architecture: `docs/architecture.md`
- Roadmap/Phases: `docs/roadmap.md`
- Macro indicator catalog: `docs/macro_indicator_catalog.md`
- Ingestion behavior/flow: `docs/ingestion_design.md`
- Storage schema/rules: `docs/storage_schema.md`
- Freshness policy: `docs/freshness_policy.md`
- Snapshot contract: `docs/snapshot_schema.md`
- Snapshot state derivation rules: `docs/state_derivation_rules.md`
- Regime contract: `docs/regime_schema.md`
- Regime vocabulary: `docs/regime_vocabulary.md`
- Regime mapping rules: `docs/regime_mapping_rules.md`
- Regime confidence policy: `docs/regime_confidence_policy.md`
- Regime builder: `docs/regime_builder.md`
- Metrics reference: `docs/metrics.md`
- Deployment: `docs/deployment.md`
