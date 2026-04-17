# Decisions

## 2026-04-17 — Encode workflow as agent profile
- **Decision**: Implement the requested procedure as a repository-level Copilot agent profile (`.github/copilot-instructions.md`) plus cloud-agent setup workflow.
- **Reason**: A custom built-in "skill" cannot be created from this repository directly, but agent instructions and setup workflow provide persistent, reusable behavior for future sessions.
- **Tradeoff**: Behavior is instruction-driven rather than a separately invocable skill package.
- **Follow-up**: If a dedicated external skill registry is introduced, migrate this profile into a first-class skill.

## 2026-04-17 — Phase 1 indicator scope
- **Decision**: Start Phase 1 with a strict priority set (CPI, Unemployment, 10Y Yield, PMI, Retail Sales) instead of broad indicator expansion.
- **Reason**: The phase objective emphasizes reliability of ingestion/normalization over breadth.
- **Tradeoff**: Coverage is narrower in this task but quality and freshness tracking are testable end-to-end.
- **Follow-up**: Add remaining Phase 1 indicators in subsequent backlog tasks with the same schema/contracts.

## 2026-04-17 — Checklist-first closure
- **Decision**: Add a dedicated Phase 1 checklist audit document and explicit ingestion-throughput metric before widening indicator coverage.
- **Reason**: The immediate request prioritized checklist verification and observable ingestion foundation quality.
- **Tradeoff**: Added operational/docs artifacts before expanding additional data sources.
- **Follow-up**: Add alert rules for the new ingestion-throughput metric in a later ops-focused Phase 1 task.

## 2026-04-17 — Canonical documentation re-layering
- **Decision**: Adopt strict role separation: concise README + canonical docs + historical logs + scoped backlog.
- **Reason**: Reduce duplication/drift and make ownership of each topic explicit.
- **Tradeoff**: Existing long-form mixed docs were reduced or linked instead of repeated.
- **Follow-up**: Continue consolidating any remaining overlapping legacy docs into canonical files.

## 2026-04-17 — Phase 2 snapshot-first implementation
- **Decision**: Implement Phase 2 in order: snapshot contract → derivation logic → persistence → tests → docs.
- **Reason**: Current stage prioritizes truthful domain contracts over surface/API expansion.
- **Tradeoff**: Snapshot logic is currently service/domain-centric and not yet expanded into broader product surfaces.
- **Follow-up**: Add next Phase 2 backlog tasks for API contract wiring only after domain/persistence coverage is stable.
