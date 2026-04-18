"""Utility functions for building product DTOs from domain objects.

These helpers translate internal domain models into frontend-friendly
DTOs without leaking domain internals into the product surface.

All functions are pure and deterministic.
"""

from __future__ import annotations

from apps.api.dto.signals import SignalSummaryDTO
from apps.api.dto.snapshots import FeatureDeltaDTO, FeatureDTO
from apps.api.dto.trust import DataAvailability, FreshnessStatus, SourceAttribution, TrustMetadata
from domain.macro.comparison import FeatureDelta, SnapshotComparison
from domain.macro.models import MacroFeature, MacroSnapshot
from domain.signals.models import SignalOutput, SignalResult

# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------

_INDICATOR_LABELS: dict[str, str] = {
    "gdp": "GDP Growth",
    "inflation": "Inflation",
    "unemployment": "Unemployment Rate",
    "interest_rate": "Interest Rate",
    "exchange_rate": "Exchange Rate",
    "stock_index": "Stock Index",
    "bond_yield": "Bond Yield",
    "credit_spread": "Credit Spread",
    "commodity_price": "Commodity Price",
    "pmi": "PMI",
}

_SOURCE_LABELS: dict[str, str] = {
    "fred": "FRED — Federal Reserve",
    "world_bank": "World Bank",
    "imf": "IMF",
    "oecd": "OECD",
    "ecb": "ECB — European Central Bank",
    "market_data": "Market Data",
    "custom": "Custom",
    "synthetic": "Synthetic (placeholder)",
}


def _indicator_label(indicator_type: str) -> str:
    return _INDICATOR_LABELS.get(indicator_type, indicator_type.replace("_", " ").title())


def _source_label(source_id: str) -> str:
    return _SOURCE_LABELS.get(source_id, source_id.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Trust metadata builders
# ---------------------------------------------------------------------------


def build_trust_from_snapshot(snapshot: MacroSnapshot) -> TrustMetadata:
    """Build :class:`~apps.api.dto.trust.TrustMetadata` from a domain snapshot.

    Freshness is always ``FRESH`` for a live-fetched snapshot; staleness
    detection requires a maximum-age policy (deferred to a future enhancement).
    """
    source_ids: list[str] = list(
        {str(f.source) for f in snapshot.features}
    )
    sources = [
        SourceAttribution(
            source_id=sid,
            source_label=_source_label(sid),
            retrieval_timestamp=snapshot.snapshot_time,
        )
        for sid in source_ids
    ]
    return TrustMetadata(
        snapshot_timestamp=snapshot.snapshot_time,
        freshness_status=FreshnessStatus.FRESH,
        availability=DataAvailability.FULL if snapshot.features else DataAvailability.UNAVAILABLE,
        is_degraded=False,
        sources=sources,
    )


def build_trust_from_comparison(
    comparison: SnapshotComparison,
    current_snapshot: MacroSnapshot,
    prior_snapshot_timestamp: object | None = None,
) -> TrustMetadata:
    """Build :class:`~apps.api.dto.trust.TrustMetadata` for a comparison response."""
    base = build_trust_from_snapshot(current_snapshot)
    availability = DataAvailability.FULL
    if comparison.no_prior_count > 0 and comparison.no_prior_count == len(comparison.deltas):
        availability = DataAvailability.UNAVAILABLE
    elif comparison.no_prior_count > 0:
        availability = DataAvailability.PARTIAL

    from datetime import datetime

    prior_ts: datetime | None = None
    if isinstance(prior_snapshot_timestamp, datetime):
        prior_ts = prior_snapshot_timestamp

    return TrustMetadata(
        snapshot_timestamp=base.snapshot_timestamp,
        previous_snapshot_timestamp=prior_ts,
        freshness_status=base.freshness_status,
        availability=availability,
        is_degraded=availability == DataAvailability.DEGRADED,
        sources=base.sources,
        changed_indicators_count=comparison.changed_count,
    )


def build_trust_from_signal_result(
    result: SignalResult,
) -> TrustMetadata:
    """Build :class:`~apps.api.dto.trust.TrustMetadata` for a signal result."""
    base = build_trust_from_snapshot(result.macro_snapshot)
    availability = DataAvailability.FULL if result.signals else DataAvailability.PARTIAL
    if not result.success:
        availability = DataAvailability.UNAVAILABLE
    return TrustMetadata(
        snapshot_timestamp=base.snapshot_timestamp,
        freshness_status=base.freshness_status,
        availability=availability,
        is_degraded=not result.success,
        sources=base.sources,
    )


# ---------------------------------------------------------------------------
# Domain → DTO converters
# ---------------------------------------------------------------------------


def feature_to_dto(feature: MacroFeature) -> FeatureDTO:
    """Convert a domain :class:`~domain.macro.models.MacroFeature` to :class:`FeatureDTO`."""
    return FeatureDTO(
        indicator_type=str(feature.indicator_type),
        indicator_label=_indicator_label(str(feature.indicator_type)),
        value=feature.value,
        source_id=str(feature.source),
        frequency=str(feature.frequency),
        country=feature.country,
        observed_at=feature.timestamp,
    )


def delta_to_dto(delta: FeatureDelta) -> FeatureDeltaDTO:
    """Convert a domain :class:`~domain.macro.comparison.FeatureDelta` to :class:`FeatureDeltaDTO`."""
    return FeatureDeltaDTO(
        indicator_type=delta.indicator_type,
        indicator_label=_indicator_label(delta.indicator_type),
        current_value=delta.current_value,
        prior_value=delta.prior_value,
        delta=delta.delta,
        direction=delta.direction,
        is_significant=False,
    )


def signal_output_to_dto(signal: SignalOutput) -> SignalSummaryDTO:
    """Convert a domain :class:`~domain.signals.models.SignalOutput` to :class:`SignalSummaryDTO`."""
    rules_total = len(signal.rule_results)
    rules_passed = sum(1 for v in signal.rule_results.values() if v)
    return SignalSummaryDTO(
        signal_id=signal.signal_id,
        signal_type=str(signal.signal_type),
        strength=str(signal.strength),
        score=signal.score,
        trend=str(signal.trend),
        rationale=signal.rationale,
        triggered_at=signal.triggered_at,
        rule_results=signal.rule_results,
        rules_passed=rules_passed,
        rules_total=rules_total,
        asset_class=signal.asset_class,
        supporting_regime=signal.supporting_regime,
        supporting_drivers=list(signal.supporting_drivers),
        conflicting_drivers=list(signal.conflicting_drivers),
    )
