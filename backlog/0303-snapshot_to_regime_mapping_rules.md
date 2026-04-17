# 0303 — Snapshot to regime mapping rules

Status: DONE
Completed: 2026-04-17T15:06:30.000Z
Commit: feat(regime): add deterministic snapshot-to-regime mapping

## Goal
Define deterministic and reviewable mapping rules from snapshot states to regime labels.

## Scope
- Add explicit ordered mapping rules.
- Keep rule outputs deterministic and typed.
- Add unit tests for core and degraded/missing paths.
- Add canonical mapping rules documentation.

## Validation
- Regime mapping unit tests.
