"""Explanation read routes for the analyst-facing product API.

Routes
------
``GET /api/explanations/{id}``
    Retrieve the explanation associated with a signal engine run or snapshot
    context identified by *id*.

Design notes
------------
* In the current implementation, explanations are derived deterministically
  from the signal run output stored in-memory via the agent service.
* The route returns HTTP 404 when no explanation can be found for the given ID.
* Trust metadata marks the explanation as fresh when the run is found.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Path

from apps.api.dto.explanations import ExplanationResponse
from apps.api.dto.trust import DataAvailability, FreshnessStatus, TrustMetadata

router = APIRouter(prefix="/api/explanations", tags=["explanations"])

# ---------------------------------------------------------------------------
# In-memory explanation store (placeholder for Phase 6 MVP)
# ---------------------------------------------------------------------------
# A real implementation would query a repository.  For Phase 6 MVP we store
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
    "/{explanation_id}",
    response_model=ExplanationResponse,
    summary="Get explanation by ID",
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
) -> ExplanationResponse:
    """Build and store a deterministic explanation for a signal run.

    Args:
        run_id: The signal engine run identifier.
        signal_id: The specific signal; ``None`` for run-level explanations.
        summary: Short summary text.
        rationale_points: Supporting bullet points.

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
        generated_at=datetime.now(UTC),
        trust=TrustMetadata(
            freshness_status=FreshnessStatus.FRESH,
            availability=DataAvailability.FULL,
            is_degraded=False,
        ),
    )
    register_explanation(explanation)
    return explanation
