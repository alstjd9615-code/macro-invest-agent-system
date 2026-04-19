# macro-invest-agent-platform

Macroeconomic data ingestion and analysis platform for deterministic investment research workflows.

## Why this exists

- Build a reliable macro data foundation (ingestion, normalization, freshness).
- Keep deterministic domain outputs as the source of truth.
- Separate data/logic layers from agent-facing interfaces.

## Current status

- **Phase 1 (Macro Data Foundation): baseline complete**
- **Phase 2 (Macro Snapshot Layer): baseline complete**
- **Phase 3 (Macro Regime Engine): baseline complete**
- **Active workstream — Multi-Engine Analysis Hub:**
  - ✅ Quant Scoring Engine v1 (`domain/quant/`)
  - ✅ Confidence Refactor — quant-informed regime + signal confidence
  - ✅ Conflict Surface v1 — explicit mixed/low-conviction signal semantics

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

- **Domain/Core**: deterministic macro, snapshot, regime, quant-score, and conflict models/rules.
- **Pipelines**: macro ingestion and normalization workflows.
- **Snapshot layer**: deterministic macro state structuring and comparison.
- **Regime layer**: deterministic snapshot-to-regime contract and classification.
- **Quant Scoring Engine**: dimension scores (growth/inflation/labor/policy/financial conditions)
  plus secondary measures (breadth, momentum, change intensity, overall support).
- **Confidence layer**: regime and signal confidence informed by quant scores, freshness, and
  degraded status.
- **Conflict Surface**: explicit conflict/conviction status (clean / tension / mixed /
  low_conviction) distinguishing analytical tension from data quality issues.
- **API**: analyst-facing read API (signals/explanations are currently experimental surfaces).
- **Observability**: Prometheus metrics + Grafana dashboards.

## Key semantic distinctions

| Concept | Meaning | Field |
|---|---|---|
| **Degraded** | Data/freshness/quality problem | `is_degraded`, `caveat` |
| **Mixed / Conflicted** | Analytical tension between macro drivers | `is_mixed`, `conflict_status` |
| **Low confidence** | Regime label has insufficient analytical certainty | `confidence` |

## Canonical documentation

- Architecture: `docs/architecture.md`
- Roadmap/Phases: `docs/roadmap.md`
- Macro indicator catalog: `docs/macro_indicator_catalog.md`
- Ingestion behavior/flow: `docs/ingestion_design.md`
- Storage schema/rules: `docs/storage_schema.md`
- Freshness policy: `docs/freshness_policy.md`
- Snapshot contract: `docs/snapshot_schema.md`
- Snapshot state derivation rules: `docs/state_derivation_rules.md`
- Regime engine docs index: `docs/regime_engine.md`
- Regime confidence policy (updated): `docs/regime_confidence_policy.md`
- Conflict Surface v1: `docs/conflict_surface_v1.md`
- Legacy surface status: `docs/legacy_surface_status.md`
- CI/CD quick guide: `docs/ci_cd.md`
- Metrics reference: `docs/metrics.md`
- Deployment: `docs/deployment.md`
