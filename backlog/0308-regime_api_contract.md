# 0308 — Regime API contract

Status: DONE
Completed: 2026-04-17T15:27:40.000Z
Commit: feat(api): add regime read contract endpoints

## Goal
Expose persisted regime and transition state through analyst-facing read API endpoints.

## Scope
- Add regime DTOs.
- Add `/api/regimes/latest` and `/api/regimes/compare` read routes.
- Add dependency provider for regime service.
- Add API router tests.
- Add canonical API contract doc.

## Validation
- Regime router tests.
