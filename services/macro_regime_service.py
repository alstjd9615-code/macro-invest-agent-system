"""Phase 3 service for building macro regimes from stored snapshots."""

from __future__ import annotations

from datetime import date

from core.contracts.macro_snapshot_repository import MacroSnapshotRepositoryContract
from domain.macro.regime import MacroRegime
from domain.macro.regime_mapping import (
    build_regime_rationale,
    derive_regime_confidence,
    derive_regime_missing_inputs,
    map_snapshot_to_regime,
)


class MacroRegimeService:
    """Build deterministic macro regimes for a selected as-of date."""

    def __init__(self, snapshot_repository: MacroSnapshotRepositoryContract) -> None:
        self._snapshot_repository = snapshot_repository

    async def build_regime(self, as_of_date: date) -> MacroRegime:
        snapshot = await self._snapshot_repository.get_latest_on_or_before(as_of_date)
        if snapshot is None:
            raise ValueError(f"No snapshot available on or before {as_of_date.isoformat()}")

        label, family = map_snapshot_to_regime(snapshot)
        return MacroRegime(
            as_of_date=snapshot.as_of_date,
            regime_label=label,
            regime_family=family,
            supporting_snapshot_id=snapshot.snapshot_id,
            supporting_states={
                "growth_state": snapshot.growth_state.value,
                "inflation_state": snapshot.inflation_state.value,
                "labor_state": snapshot.labor_state.value,
                "policy_state": snapshot.policy_state.value,
                "financial_conditions_state": snapshot.financial_conditions_state.value,
            },
            confidence=derive_regime_confidence(snapshot=snapshot, label=label),
            freshness_status=snapshot.freshness_status,
            degraded_status=snapshot.degraded_status,
            missing_inputs=derive_regime_missing_inputs(snapshot),
            rationale_summary=build_regime_rationale(snapshot=snapshot, label=label),
        )
