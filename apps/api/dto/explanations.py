"""Explanation DTOs for the analyst-facing read API.

These models are the stable, frontend-friendly contracts for:

* ``GET /api/explanations/{id}`` — retrieve the explanation associated with a
  signal run or snapshot context.

Design notes
------------
* An ``Explanation`` links a human-readable ``summary`` to the specific
  ``run_id`` or ``snapshot_context_id`` that generated it.
* ``rationale_points`` is a structured list for rendering bullet points in
  the workbench explanation panel.
* Trust metadata is included so stale or degraded explanations are visibly
  surfaced in the UI.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from apps.api.dto.trust import TrustMetadata


class ExplanationResponse(BaseModel, extra="forbid"):
    """Response for GET /api/explanations/{id}.

    Attributes:
        explanation_id: Unique explanation identifier (typically the run ID
            or a composite of run ID + signal ID).
        run_id: Signal engine run this explanation is associated with.
        signal_id: Signal this explanation describes; ``None`` for snapshot-level
            explanations.
        summary: Short, human-readable explanation of the signal or snapshot
            state.
        rationale_points: Ordered list of supporting rationale bullet points.
        generated_at: Timestamp when this explanation was produced.
        trust: Trust and freshness metadata.
    """

    explanation_id: str = Field(..., description="Unique explanation identifier")
    run_id: str = Field(..., description="Signal engine run this explanation is tied to")
    signal_id: str | None = Field(
        default=None,
        description="Signal this explanation describes; None for snapshot-level explanations",
    )
    summary: str = Field(default="", description="Short human-readable explanation summary")
    rationale_points: list[str] = Field(
        default_factory=list,
        description="Supporting rationale bullet points in display order",
    )
    generated_at: datetime = Field(..., description="Timestamp when this explanation was produced")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
