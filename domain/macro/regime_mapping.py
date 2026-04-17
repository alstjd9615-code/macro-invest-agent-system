"""Deterministic Phase 3 rules mapping snapshot states to regime labels."""

from __future__ import annotations

from domain.macro.regime import RegimeFamily, RegimeLabel, regime_family_for_label
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


def _has_unknown_state(snapshot: MacroSnapshotState) -> bool:
    states = (
        snapshot.growth_state,
        snapshot.inflation_state,
        snapshot.labor_state,
        snapshot.policy_state,
        snapshot.financial_conditions_state,
    )
    return any(str(state).endswith("unknown") for state in states)


def map_snapshot_to_regime_label(snapshot: MacroSnapshotState) -> RegimeLabel:
    """Map a macro snapshot to a regime label using explicit rule order."""
    if snapshot.degraded_status in {
        DegradedStatus.MISSING,
        DegradedStatus.SOURCE_UNAVAILABLE,
    }:
        return RegimeLabel.UNCLEAR
    if snapshot.freshness_status in {FreshnessStatus.STALE, FreshnessStatus.UNKNOWN}:
        return RegimeLabel.UNCLEAR
    if _has_unknown_state(snapshot):
        return RegimeLabel.MIXED

    if (
        snapshot.growth_state == GrowthState.ACCELERATING
        and snapshot.inflation_state == InflationState.COOLING
        and snapshot.labor_state in {LaborState.TIGHT, LaborState.SOFTENING}
        and snapshot.policy_state in {PolicyState.NEUTRAL, PolicyState.EASING_BIAS}
        and snapshot.financial_conditions_state
        in {FinancialConditionsState.NEUTRAL, FinancialConditionsState.LOOSE}
    ):
        return RegimeLabel.GOLDILOCKS

    if snapshot.inflation_state == InflationState.COOLING and snapshot.growth_state in {
        GrowthState.MIXED,
        GrowthState.SLOWING,
    }:
        return RegimeLabel.DISINFLATION

    if (
        snapshot.growth_state == GrowthState.SLOWING
        and snapshot.labor_state == LaborState.WEAK
        and snapshot.policy_state == PolicyState.RESTRICTIVE
        and snapshot.financial_conditions_state == FinancialConditionsState.TIGHT
    ):
        return RegimeLabel.CONTRACTION

    if (
        snapshot.policy_state == PolicyState.RESTRICTIVE
        and snapshot.financial_conditions_state == FinancialConditionsState.TIGHT
        and snapshot.growth_state in {GrowthState.SLOWING, GrowthState.MIXED}
    ):
        return RegimeLabel.POLICY_TIGHTENING_DRAG

    if (
        snapshot.growth_state == GrowthState.SLOWING
        and snapshot.inflation_state == InflationState.REACCELERATING
        and snapshot.labor_state in {LaborState.SOFTENING, LaborState.WEAK}
    ):
        return RegimeLabel.STAGFLATION_RISK

    if (
        snapshot.inflation_state == InflationState.REACCELERATING
        and snapshot.growth_state in {GrowthState.ACCELERATING, GrowthState.MIXED}
        and snapshot.policy_state == PolicyState.EASING_BIAS
    ):
        return RegimeLabel.REFLATION

    if (
        snapshot.growth_state == GrowthState.SLOWING
        and snapshot.labor_state in {LaborState.SOFTENING, LaborState.WEAK}
        and snapshot.inflation_state in {InflationState.STICKY, InflationState.COOLING}
    ):
        return RegimeLabel.SLOWDOWN

    return RegimeLabel.MIXED


def map_snapshot_to_regime(snapshot: MacroSnapshotState) -> tuple[RegimeLabel, RegimeFamily]:
    label = map_snapshot_to_regime_label(snapshot)
    return label, regime_family_for_label(label)


def build_regime_rationale(snapshot: MacroSnapshotState, label: RegimeLabel) -> str:
    return (
        "growth="
        f"{snapshot.growth_state.value}, inflation={snapshot.inflation_state.value}, "
        f"labor={snapshot.labor_state.value}, policy={snapshot.policy_state.value}, "
        f"financial_conditions={snapshot.financial_conditions_state.value}, "
        f"label={label.value}"
    )
