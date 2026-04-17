# 0307 — Regime transition logic

Status: DONE
Completed: 2026-04-17T15:22:10.000Z
Commit: feat(regime): add deterministic regime transition logic

## Goal
Add deterministic current-vs-prior regime transition classification.

## Scope
- Add transition derivation utility.
- Wire transition assignment into regime build-and-save flow.
- Add unit tests for initial/shift/strengthening/weakening/unchanged paths.
- Add canonical transition rules documentation.

## Validation
- Transition unit tests and service transition tests.
