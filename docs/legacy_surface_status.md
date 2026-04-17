# Legacy Surface Status

This document tracks active pre-realignment product surfaces that are still
present in the repository.

## Experimental surfaces (active)

1. `GET /api/signals/latest`
   - Status: **Experimental**
   - Reason: signal rules and scoring are still placeholder-weighted in parts of
     the signal engine/rule layer.

2. `GET /api/explanations/{id}`
   - Status: **Experimental**
   - Reason: explanation retrieval is in-memory and derived from signal output,
     not a finalized persisted explanation workflow.

3. Frontend signals/explanations sections
   - Status: **Experimental**
   - Reason: these sections render the same experimental signal/explanation APIs.

## Non-experimental current core

- Ingestion foundation (Phase 1)
- Snapshot contract/derivation/comparison (Phase 2)
- Regime contract/mapping/confidence/transition/persistence/read API (Phase 3)

## Cleanup policy

- Keep experimental surfaces visible only with explicit experimental labeling.
- Do not present experimental outputs as production-grade inference.
- Prefer narrowing labels and scope over feature expansion.
