# 0301 — Regime schema definition

Status: DONE
Completed: 2026-04-17T14:54:14.517Z
Commit: feat(regime): define macro regime schema contract

## Goal
Define the canonical Phase 3 macro regime schema and vocabulary as typed domain contracts.

## Scope
- Add regime schema model(s) for label/family/confidence/freshness/degraded/transition fields.
- Add deterministic vocabulary enums for labels, families, confidence levels, and transition types.
- Add schema-focused unit tests.
- Add canonical regime schema documentation.

## Validation
- Regime schema unit tests.
- Existing snapshot domain tests as regression sanity check.
