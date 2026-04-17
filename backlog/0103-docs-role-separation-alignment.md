# 0103 — Documentation role separation alignment

Status: DONE
Completed: 2026-04-17T13:57:31.187Z
Commit: docs(structure): align repo docs to role-separated canonical policy

## Goal
Align repository documentation structure with the policy:
README as entrypoint, `/docs` as canonical references, `/logs` as history, `/backlog` as execution queue.

## Scope
- Create canonical docs if missing:
  - `docs/architecture.md`
  - `docs/roadmap.md`
  - `docs/macro_indicator_catalog.md`
  - `docs/ingestion_design.md`
  - `docs/storage_schema.md`
  - `docs/freshness_policy.md`
- Simplify README to concise entry-level content with links.
- Remove or shrink overlapping docs by linking to canonical files.

## Validation
- Documentation consistency check (no overlapping long duplicate explanations across README/docs/logs/backlog).
