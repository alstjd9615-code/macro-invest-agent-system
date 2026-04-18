"""Tests for the startup seeder — seed_regime_from_synthetic_observations."""

from __future__ import annotations

from datetime import date

import pytest

from adapters.repositories.in_memory_macro_regime_store import InMemoryMacroRegimeStore
from adapters.repositories.in_memory_macro_snapshot_store import InMemoryMacroSnapshotStore
from apps.api.startup_seeder import seed_regime_from_synthetic_observations
from domain.macro.regime import RegimeLabel
from services.macro_regime_service import MacroRegimeService
from services.macro_snapshot_service import MacroSnapshotService


@pytest.fixture()
def snapshot_store() -> InMemoryMacroSnapshotStore:
    return InMemoryMacroSnapshotStore()


@pytest.fixture()
def regime_store() -> InMemoryMacroRegimeStore:
    return InMemoryMacroRegimeStore()


@pytest.fixture()
def snapshot_service(snapshot_store: InMemoryMacroSnapshotStore) -> MacroSnapshotService:
    return MacroSnapshotService(repository=snapshot_store)


@pytest.fixture()
def regime_service(
    snapshot_store: InMemoryMacroSnapshotStore,
    regime_store: InMemoryMacroRegimeStore,
) -> MacroRegimeService:
    return MacroRegimeService(
        snapshot_repository=snapshot_store,
        regime_repository=regime_store,
    )


@pytest.mark.asyncio
async def test_seeder_populates_regime_store(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
    regime_store: InMemoryMacroRegimeStore,
) -> None:
    """After seeding, the regime store contains exactly one regime."""
    assert regime_store.all_regimes() == []

    await seed_regime_from_synthetic_observations(
        snapshot_service=snapshot_service,
        regime_service=regime_service,
        as_of_date=date(2026, 4, 1),
    )

    regimes = regime_store.all_regimes()
    assert len(regimes) == 1


@pytest.mark.asyncio
async def test_seeder_regime_has_known_label(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
    regime_store: InMemoryMacroRegimeStore,
) -> None:
    """The seeded regime label must be a valid, non-UNCLEAR label."""
    await seed_regime_from_synthetic_observations(
        snapshot_service=snapshot_service,
        regime_service=regime_service,
        as_of_date=date(2026, 4, 1),
    )

    regime = regime_store.all_regimes()[0]
    # Synthetic values should produce a deterministic non-UNCLEAR regime
    assert regime.regime_label in {
        RegimeLabel.SLOWDOWN,
        RegimeLabel.POLICY_TIGHTENING_DRAG,
        RegimeLabel.STAGFLATION_RISK,
        RegimeLabel.CONTRACTION,
    }


@pytest.mark.asyncio
async def test_seeder_regime_is_retrievable_via_service(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
) -> None:
    """After seeding, get_latest_regime returns the seeded regime."""
    target = date(2026, 4, 1)
    await seed_regime_from_synthetic_observations(
        snapshot_service=snapshot_service,
        regime_service=regime_service,
        as_of_date=target,
    )

    regime = await regime_service.get_latest_regime(as_of_date=target)
    assert regime is not None
    assert regime.as_of_date == target


@pytest.mark.asyncio
async def test_seeder_regime_transition_is_initial(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
) -> None:
    """The first seeded regime has transition_type=initial (no prior baseline)."""
    await seed_regime_from_synthetic_observations(
        snapshot_service=snapshot_service,
        regime_service=regime_service,
        as_of_date=date(2026, 4, 1),
    )

    regime = await regime_service.get_latest_regime(as_of_date=date(2026, 4, 1))
    assert regime is not None
    assert regime.transition.transition_type.value == "initial"


@pytest.mark.asyncio
async def test_seeder_snapshot_is_populated(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
    snapshot_store: InMemoryMacroSnapshotStore,
) -> None:
    """After seeding, the snapshot store contains one snapshot with real state values."""
    await seed_regime_from_synthetic_observations(
        snapshot_service=snapshot_service,
        regime_service=regime_service,
        as_of_date=date(2026, 4, 1),
    )

    snapshots = snapshot_store.all_snapshots()
    assert len(snapshots) == 1
    snap = snapshots[0]
    # All five category states should be derived (not UNKNOWN)
    assert snap.growth_state.value != "unknown"
    assert snap.inflation_state.value != "unknown"
    assert snap.labor_state.value != "unknown"
    assert snap.policy_state.value != "unknown"
    assert snap.financial_conditions_state.value != "unknown"
