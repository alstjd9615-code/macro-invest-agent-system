# Regime Persistence

Canonical references:

- contract: `core/contracts/macro_regime_repository.py`
- in-memory adapter: `adapters/repositories/in_memory_macro_regime_store.py`

## Repository operations

- `save_regime(regime)`
- `get_regime_by_id(regime_id)`
- `get_latest_on_or_before(as_of_date)`

This phase uses an in-memory adapter for deterministic testing and local flow
validation. Durable DB-backed persistence can implement the same contract.
