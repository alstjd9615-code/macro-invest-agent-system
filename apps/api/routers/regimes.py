"""Regime read routes for the analyst-facing product API."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.dependencies import get_regime_service
from apps.api.dto.regimes import RegimeCompareResponse, RegimeLatestResponse, RegimeTransitionDTO
from domain.macro.regime import MacroRegime, RegimeConfidence, RegimeLabel
from domain.macro.snapshot import DegradedStatus
from pipelines.ingestion.models import FreshnessStatus
from services.interfaces import RegimeServiceInterface

router = APIRouter(prefix="/api/regimes", tags=["regimes"])


def _compute_regime_status(regime: MacroRegime) -> str:
    """Derive a single product-surface status token from a regime object.

    Returns one of: ``'success'``, ``'degraded'``, ``'stale'``, ``'bootstrap'``.
    Priority order: bootstrap → stale → degraded → success.
    """
    if regime.metadata.get("seeded") == "true":
        return "bootstrap"
    if regime.freshness_status in {FreshnessStatus.STALE, FreshnessStatus.UNKNOWN}:
        return "stale"
    if (
        regime.degraded_status
        in {DegradedStatus.PARTIAL, DegradedStatus.MISSING, DegradedStatus.SOURCE_UNAVAILABLE}
        or regime.confidence == RegimeConfidence.LOW
        or regime.regime_label in {RegimeLabel.MIXED, RegimeLabel.UNCLEAR}
    ):
        return "degraded"
    return "success"


def _to_latest_response(regime: MacroRegime) -> RegimeLatestResponse:
    is_seeded = regime.metadata.get("seeded") == "true"
    data_source = regime.metadata.get("source", "")
    return RegimeLatestResponse(
        as_of_date=regime.as_of_date,
        regime_id=regime.regime_id,
        regime_timestamp=regime.regime_timestamp,
        regime_label=regime.regime_label.value,
        regime_family=regime.regime_family.value,
        confidence=regime.confidence.value,
        freshness_status=regime.freshness_status.value,
        degraded_status=regime.degraded_status.value,
        missing_inputs=list(regime.missing_inputs),
        supporting_snapshot_id=regime.supporting_snapshot_id,
        supporting_states=dict(regime.supporting_states),
        transition=RegimeTransitionDTO(
            transition_from_prior=regime.transition.transition_from_prior,
            transition_type=regime.transition.transition_type.value,
            changed=regime.transition.changed,
        ),
        rationale_summary=regime.rationale_summary,
        warnings=list(regime.warnings),
        status=_compute_regime_status(regime),
        is_seeded=is_seeded,
        data_source=data_source,
    )


@router.get(
    "/latest",
    response_model=RegimeLatestResponse,
    summary="Get latest persisted macro regime",
)
async def get_latest_regime(
    as_of_date: date = Query(default_factory=date.today),
    regime_service: RegimeServiceInterface = Depends(get_regime_service),
) -> RegimeLatestResponse:
    try:
        regime = await regime_service.get_latest_regime(as_of_date=as_of_date)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if regime is None:
        raise HTTPException(status_code=404, detail="No persisted regime available")
    return _to_latest_response(regime)


@router.get(
    "/compare",
    response_model=RegimeCompareResponse,
    summary="Compare current regime against prior baseline",
)
async def compare_regimes(
    as_of_date: date = Query(default_factory=date.today),
    regime_service: RegimeServiceInterface = Depends(get_regime_service),
) -> RegimeCompareResponse:
    try:
        current, previous = await regime_service.compare_latest_with_prior(as_of_date=as_of_date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return RegimeCompareResponse(
        as_of_date=current.as_of_date,
        baseline_available=previous is not None,
        current_regime_label=current.regime_label.value,
        prior_regime_label=previous.regime_label.value if previous is not None else None,
        transition_type=current.transition.transition_type.value,
        changed=current.transition.changed,
        current_confidence=current.confidence.value,
        prior_confidence=previous.confidence.value if previous is not None else None,
        current_rationale_summary=current.rationale_summary,
        warnings=list(current.warnings),
        is_seeded=current.metadata.get("seeded") == "true",
    )
