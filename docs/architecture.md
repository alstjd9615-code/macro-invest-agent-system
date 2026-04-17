# Architecture

## Overview

The platform is layered to keep deterministic computation and operational interfaces separated.

1. **Domain/Core**  
   Deterministic macro models, validation, and signal logic.
2. **Pipelines**  
   Data ingestion, normalization, and persistence workflows.
3. **API/MCP/Agent layers**  
   Read-oriented interfaces and agent-facing orchestration.
4. **Observability**  
   Metrics, tracing, and operational dashboards.

## Design constraints

- Deterministic outputs are authoritative.
- Typed schemas at all boundaries.
- Clear separation between data foundation and higher-level interpretation.
- Observability and failure categorization are first-class.

## Related docs

- Ingestion flow: `docs/ingestion_design.md`
- Storage schema: `docs/storage_schema.md`
- Freshness rules: `docs/freshness_policy.md`
