# 0302 — Regime vocabulary definition

Status: DONE
Completed: 2026-04-17T15:00:12.968Z
Commit: feat(regime): define canonical regime vocabulary mapping

## Goal
Define and lock the canonical Phase 3 regime vocabulary used by mapping and
builder layers.

## Scope
- Define a deterministic label-to-family mapping.
- Expose mapping utilities from the macro domain layer.
- Enforce label/family consistency in the regime contract.
- Add focused tests for mapping coverage and schema enforcement.
- Add a canonical vocabulary document without duplicating schema docs.

## Validation
- Regime schema and vocabulary unit tests.
