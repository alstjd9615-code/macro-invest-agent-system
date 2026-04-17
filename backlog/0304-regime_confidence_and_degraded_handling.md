# 0304 — Regime confidence and degraded handling

Status: DONE
Completed: 2026-04-17T15:10:10.000Z
Commit: feat(regime): add confidence and degraded handling rules

## Goal
Define deterministic confidence and degraded/missing-input handling for regime outputs.

## Scope
- Add confidence derivation utility (`high|medium|low`).
- Add missing-input propagation utility.
- Add tests for fresh/late/stale and degraded paths.
- Add canonical confidence policy documentation.

## Validation
- Regime confidence unit tests.
