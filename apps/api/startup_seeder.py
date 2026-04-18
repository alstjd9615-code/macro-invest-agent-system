"""Startup seeder for the analyst-facing product API.

Seeds the shared in-memory stores with a synthetic macro snapshot and a
derived regime so that :func:`GET /api/regimes/latest` returns real data
immediately after startup instead of HTTP 404.

Design notes
------------
* Seeding uses deterministic synthetic observations derived from the
  indicator catalog.  Indicator values are chosen to produce a
  well-defined, non-trivial regime rather than all-UNKNOWN states.
* The seeder is idempotent: calling it multiple times for the same date
  simply appends another snapshot/regime for that date.  The
  ``get_latest_on_or_before`` query always returns the most recent.
* This module does **not** replace a real ingestion pipeline.  It exists
  solely to provide a non-empty initial state for the in-memory stores.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from core.logging.logger import get_logger
from domain.macro.enums import DataFrequency, MacroIndicatorType, MacroSourceType
from pipelines.ingestion.models import (
    FreshnessMetadata,
    FreshnessStatus,
    NormalizedMacroObservation,
    RevisionStatus,
)
from services.macro_regime_service import MacroRegimeService
from services.macro_snapshot_service import MacroSnapshotService

_log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Synthetic indicator values
# ---------------------------------------------------------------------------
# Values are chosen to produce a well-defined SLOWDOWN regime:
#   growth=SLOWING (PMI=48, retail_sales=−0.5) → slowing
#   inflation=STICKY (CPI=3.1) → sticky
#   labor=SOFTENING (UNRATE=4.4) → softening
#   policy=RESTRICTIVE (YIELD_10Y=4.6) → restrictive
#   financial_conditions=TIGHT (YIELD_10Y=4.6, no spread) → tight
# Outcome: SLOWDOWN (growth slowing, labor softening, inflation sticky/cooling)

_SYNTHETIC_VALUES: dict[MacroIndicatorType, float] = {
    MacroIndicatorType.PMI: 48.2,
    MacroIndicatorType.RETAIL_SALES: -0.5,
    MacroIndicatorType.INFLATION: 3.1,
    MacroIndicatorType.UNEMPLOYMENT: 4.4,
    MacroIndicatorType.YIELD_10Y: 4.6,
}


def _build_synthetic_observations(
    as_of_date: date,
    snapshot_id: str,
) -> list[NormalizedMacroObservation]:
    """Build a set of synthetic normalized observations for *as_of_date*."""
    now = datetime.now(UTC)
    obs_dt = datetime(as_of_date.year, as_of_date.month, as_of_date.day, tzinfo=UTC)
    observations: list[NormalizedMacroObservation] = []

    for indicator, value in _SYNTHETIC_VALUES.items():
        freshness = FreshnessMetadata(
            expected_max_lag_hours=24 * 45,
            observed_lag_hours=0.0,
            status=FreshnessStatus.FRESH,
            is_late=False,
            is_stale=False,
        )
        obs = NormalizedMacroObservation(
            snapshot_id=snapshot_id,
            indicator_id=indicator,
            observation_date=obs_dt,
            fetched_at=now,
            source=MacroSourceType.FRED,
            value=value,
            release_date=obs_dt,
            unit="index",
            frequency=DataFrequency.MONTHLY,
            source_series_id=f"SYNTHETIC_{indicator.value.upper()}",
            region="US",
            freshness=freshness,
            revision_status=RevisionStatus.INITIAL,
        )
        observations.append(obs)

    return observations


async def seed_regime_from_synthetic_observations(
    snapshot_service: MacroSnapshotService,
    regime_service: MacroRegimeService,
    as_of_date: date | None = None,
) -> None:
    """Seed the in-memory stores with a synthetic snapshot and regime.

    Args:
        snapshot_service: A :class:`~services.macro_snapshot_service.MacroSnapshotService`
            wired to the shared in-memory snapshot store.
        regime_service: A :class:`~services.macro_regime_service.MacroRegimeService`
            wired to the same snapshot store and to the shared regime store.
        as_of_date: Date for the synthetic data.  Defaults to today (UTC).
    """
    target_date = as_of_date or date.today()
    snapshot_id = str(uuid.uuid4())
    observations = _build_synthetic_observations(
        as_of_date=target_date,
        snapshot_id=snapshot_id,
    )

    _log.info(
        "startup_seeder_building_snapshot",
        as_of_date=str(target_date),
        indicator_count=len(observations),
    )
    snapshot = await snapshot_service.build_and_save_snapshot(
        observations=observations,
        as_of_date=target_date,
    )
    _log.info(
        "startup_seeder_snapshot_saved",
        snapshot_id=snapshot.snapshot_id,
        growth_state=snapshot.growth_state.value,
        inflation_state=snapshot.inflation_state.value,
        labor_state=snapshot.labor_state.value,
        policy_state=snapshot.policy_state.value,
        financial_conditions_state=snapshot.financial_conditions_state.value,
    )

    regime = await regime_service.build_and_save_regime(as_of_date=target_date)
    _log.info(
        "startup_seeder_regime_saved",
        regime_id=regime.regime_id,
        regime_label=regime.regime_label.value,
        regime_family=regime.regime_family.value,
        confidence=regime.confidence.value,
    )
