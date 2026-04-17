# 0101 — Phase 1 priority ingestion foundation

Status: DONE
Completed: 2026-04-17T13:27:10.116Z
Commit: feat(ingestion): implement phase1 priority data foundation

## Goal
Implement the Phase 1 macro data foundation for a small, high-priority indicator set:
CPI, Unemployment Rate, 10Y Yield, PMI, Retail Sales.

## Scope
- Define indicator catalog with frequency/unit/source/series metadata.
- Ensure source mapping exists for the priority indicator set.
- Persist raw payload records separately from normalized observations.
- Add normalized schema fields including observation/release/fetched timestamps.
- Track ingestion runs with basic success and coverage counters.
- Add baseline freshness statuses (`fresh`, `late`, `stale`, `unknown`).
- Document Phase 1 data foundation behavior.

## Validation
- Unit tests for catalog/mapping/normalization/storage/run-tracking.
- Existing ingestion pipeline tests for regression.
