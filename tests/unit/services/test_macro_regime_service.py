"""Tests for building deterministic macro regimes from snapshots."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from adapters.repositories.in_memory_macro_snapshot_store import InMemoryMacroSnapshotStore
from domain.macro.regime import RegimeConfidence, RegimeLabel
from domain.macro.snapshot import (
    DegradedStatus,
    FinancialConditionsState,
    GrowthState,
    InflationState,
    LaborState,
    MacroSnapshotState,
    PolicyState,
)
from pipelines.ingestion.models import FreshnessStatus
from services.macro_regime_service import MacroRegimeService


def _snapshot(
    *,
    as_of_date: date,
    growth: GrowthState,
    inflation: InflationState,
    labor: LaborState,
    policy: PolicyState,
    conditions: FinancialConditionsState,
    freshness: FreshnessStatus = FreshnessStatus.FRESH,
    degraded: DegradedStatus = DegradedStatus.NONE,
) -> MacroSnapshotState:
    return MacroSnapshotState(
        as_of_date=as_of_date,
        snapshot_timestamp=datetime(2026, 2, 1, tzinfo=UTC),
        freshness_status=freshness,
        degraded_status=degraded,
        growth_state=growth,
        inflation_state=inflation,
        labor_state=labor,
        policy_state=policy,
        financial_conditions_state=conditions,
        indicator_values={"inflation": 2.2},
    )


@pytest.mark.asyncio
class TestMacroRegimeService:
    async def test_build_regime_from_latest_snapshot(self) -> None:
        repo = InMemoryMacroSnapshotStore()
        await repo.save_snapshot(
            _snapshot(
                as_of_date=date(2026, 2, 1),
                growth=GrowthState.ACCELERATING,
                inflation=InflationState.COOLING,
                labor=LaborState.TIGHT,
                policy=PolicyState.NEUTRAL,
                conditions=FinancialConditionsState.NEUTRAL,
            )
        )

        svc = MacroRegimeService(snapshot_repository=repo)
        regime = await svc.build_regime(as_of_date=date(2026, 2, 1))

        assert regime.as_of_date == date(2026, 2, 1)
        assert regime.regime_label == RegimeLabel.GOLDILOCKS
        assert regime.confidence == RegimeConfidence.HIGH
        assert regime.supporting_states["growth_state"] == "accelerating"

    async def test_build_regime_uses_latest_on_or_before(self) -> None:
        repo = InMemoryMacroSnapshotStore()
        await repo.save_snapshot(
            _snapshot(
                as_of_date=date(2026, 1, 31),
                growth=GrowthState.SLOWING,
                inflation=InflationState.STICKY,
                labor=LaborState.WEAK,
                policy=PolicyState.RESTRICTIVE,
                conditions=FinancialConditionsState.TIGHT,
            )
        )
        svc = MacroRegimeService(snapshot_repository=repo)
        regime = await svc.build_regime(as_of_date=date(2026, 2, 2))
        assert regime.as_of_date == date(2026, 1, 31)

    async def test_build_regime_raises_without_snapshot(self) -> None:
        svc = MacroRegimeService(snapshot_repository=InMemoryMacroSnapshotStore())
        with pytest.raises(ValueError, match="No snapshot available"):
            await svc.build_regime(as_of_date=date(2026, 2, 1))
