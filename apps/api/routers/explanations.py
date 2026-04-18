"""Explanation read routes for the analyst-facing product API.

Routes
------
``GET /api/explanations/regime/latest``
    Return an analyst-facing narrative explanation for the current macro regime.
    Grounded in the persisted regime label, supporting states, confidence, and
    transition.

``GET /api/explanations/{id}``
    Retrieve the explanation associated with a signal engine run or snapshot
    context identified by *id*.

Design notes
------------
* Regime-level explanations are built deterministically from the persisted
  regime using :func:`~domain.macro.narrative_builder.build_regime_narrative`.
* Signal-run explanations are stored in-memory and keyed by run/signal ID.
* Trust metadata marks the explanation as fresh when the run is found.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path

from apps.api.dependencies import get_regime_service
from apps.api.dto.explanations import ExplanationResponse
from apps.api.dto.trust import DataAvailability, FreshnessStatus, TrustMetadata
from domain.macro.narrative_builder import build_regime_narrative
from services.interfaces import RegimeServiceInterface

router = APIRouter(prefix="/api/explanations", tags=["explanations"])

# ---------------------------------------------------------------------------
# In-memory explanation store (experimental surface)
# ---------------------------------------------------------------------------
# A durable implementation would query a repository. For the current experimental
# surface, we store
# explanations keyed by their ID so that tests and the workbench can
# round-trip against the API.

_store: dict[str, ExplanationResponse] = {}


def register_explanation(explanation: ExplanationResponse) -> None:
    """Register an explanation in the in-memory store.

    Called by the signals router (or tests) after a run completes so that
    ``GET /api/explanations/{id}`` can retrieve it.
    """
    _store[explanation.explanation_id] = explanation


def clear_explanation_store() -> None:
    """Clear the in-memory explanation store.  Used in tests."""
    _store.clear()


@router.get(
    "/regime/latest",
    response_model=ExplanationResponse,
    summary="Get analyst narrative for the current macro regime",
    description=(
        "Return a structured analyst-facing narrative explanation for the current "
        "persisted macro regime.  The explanation includes a concise summary paragraph, "
        "supporting rationale bullet points (regime label, supporting states, confidence, "
        "freshness, transition), and regime context metadata.  Returns 404 when no "
        "persisted regime is available."
    ),
)
async def get_regime_explanation(
    regime_service: RegimeServiceInterface = Depends(get_regime_service),
) -> ExplanationResponse:
    """Build and return an analyst narrative for the latest persisted regime.

    Returns HTTP 200 with :class:`~apps.api.dto.explanations.ExplanationResponse`
    on success.  Returns HTTP 404 when no persisted regime is available.
    """
    from datetime import date

    try:
        regime = await regime_service.get_latest_regime(as_of_date=date.today())
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if regime is None:
        raise HTTPException(
            status_code=404,
            detail="No persisted regime available for narrative explanation.",
        )

    narrative = build_regime_narrative(regime)

    is_degraded = regime.freshness_status in {
        FreshnessStatus.STALE,
        FreshnessStatus.UNKNOWN,
    } or str(regime.degraded_status) not in {"none", "DegradedStatus.NONE"}
    availability = (
        DataAvailability.PARTIAL
        if str(regime.degraded_status)
        not in {"none", "DegradedStatus.NONE", "DegradedStatus.UNKNOWN"}
        else DataAvailability.FULL
    )

    return ExplanationResponse(
        explanation_id=f"regime:{regime.regime_id}",
        run_id=regime.regime_id,
        signal_id=None,
        summary=str(narrative["summary"]),
        rationale_points=[str(p) for p in narrative["rationale_points"]],  # type: ignore[arg-type]
        regime_label=str(narrative["regime_label"]),
        regime_context={k: str(v) for k, v in narrative["regime_context"].items()},  # type: ignore[union-attr]
        generated_at=datetime.now(UTC),
        trust=TrustMetadata(
            freshness_status=FreshnessStatus(regime.freshness_status.value),
            availability=availability,
            is_degraded=is_degraded,
        ),
    )


@router.get(
    "/{explanation_id}",
    response_model=ExplanationResponse,
    summary="Get experimental explanation by ID",
    description=(
        "Retrieve the explanation associated with a signal engine run or snapshot "
        "context. The explanation includes a short summary, supporting rationale "
        "bullet points, and trust metadata. Returns 404 if not found."
    ),
)
async def get_explanation(
    explanation_id: str = Path(
        ...,
        description="Explanation ID (typically the signal engine run_id or composite ID)",
    ),
) -> ExplanationResponse:
    """Retrieve an explanation by *explanation_id*.

    Returns HTTP 200 with :class:`~apps.api.dto.explanations.ExplanationResponse`
    when found, or HTTP 404 when no explanation exists for the given ID.
    """
    explanation = _store.get(explanation_id)
    if explanation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Explanation '{explanation_id}' not found.",
        )
    return explanation


# ---------------------------------------------------------------------------
# Built-in explanation builder — creates a deterministic explanation from a
# signal summary text and associates it with a run_id.
# ---------------------------------------------------------------------------


def build_and_register_explanation(
    run_id: str,
    signal_id: str | None,
    summary: str,
    rationale_points: list[str],
    regime_label: str | None = None,
    regime_context: dict[str, str] | None = None,
) -> ExplanationResponse:
    """Build and store a deterministic explanation for a signal run.

    Args:
        run_id: The signal engine run identifier.
        signal_id: The specific signal; ``None`` for run-level explanations.
        summary: Short summary text.
        rationale_points: Supporting bullet points.
        regime_label: Optional regime label this explanation is grounded in.
        regime_context: Optional regime context dict for UI rendering.

    Returns:
        The newly created and registered :class:`ExplanationResponse`.
    """
    explanation_id = f"{run_id}:{signal_id}" if signal_id else run_id
    explanation = ExplanationResponse(
        explanation_id=explanation_id,
        run_id=run_id,
        signal_id=signal_id,
        summary=summary,
        rationale_points=rationale_points,
        regime_label=regime_label,
        regime_context=regime_context or {},
        generated_at=datetime.now(UTC),
        trust=TrustMetadata(
            freshness_status=FreshnessStatus.FRESH,
            availability=DataAvailability.FULL,
            is_degraded=False,
        ),
    )
    register_explanation(explanation)
    return explanation
