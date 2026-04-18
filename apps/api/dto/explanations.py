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
    """Response for GET /api/explanations/{id} and GET /api/explanations/regime/latest.

    Attributes:
        explanation_id: Unique explanation identifier.
        run_id: Signal engine run or regime ID this explanation is associated with.
        signal_id: Signal this explanation describes; ``None`` for regime-level explanations.
        summary: Concise analyst-facing interpretation paragraph.
        rationale_points: Ordered supporting bullet points (regime states, confidence, etc.).
        caveats: Caveats about interpretation limits (e.g. "single-indicator regime",
            "no prior baseline available for transition comparison").
        data_quality_notes: Data quality warnings surfaced to analysts (e.g. stale data,
            missing indicators, degraded snapshot).
        regime_label: Regime label this explanation is grounded in, if available.
        regime_context: Key/value regime metadata for UI rendering.

            **Minimum documented keys** (populated when a regime is available):

            * ``label``          — regime label value (e.g. ``"goldilocks"``)
            * ``family``         — regime family value (e.g. ``"expansion"``)
            * ``confidence``     — regime confidence (``"high"`` / ``"medium"`` / ``"low"``)
            * ``transition``     — transition type (``"initial"`` / ``"shift"`` / etc.)
            * ``freshness``      — freshness status (``"fresh"`` / ``"late"`` / ``"stale"``)
            * ``degraded_status``— degraded status (``"none"`` / ``"partial"`` / etc.)

        generated_at: Timestamp when this explanation was produced.
        trust: Trust and freshness metadata.
    """

    explanation_id: str = Field(..., description="Unique explanation identifier")
    run_id: str = Field(..., description="Signal engine run or regime ID this explanation is for")
    signal_id: str | None = Field(
        default=None,
        description="Signal this explanation describes; None for regime-level explanations",
    )
    summary: str = Field(default="", description="Concise analyst-facing interpretation paragraph")
    rationale_points: list[str] = Field(
        default_factory=list,
        description="Supporting rationale bullet points in display order",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description=(
            "Caveats about interpretation limits "
            "(e.g. 'no prior baseline', 'single-indicator regime')."
        ),
    )
    data_quality_notes: list[str] = Field(
        default_factory=list,
        description=(
            "Data quality warnings for analysts "
            "(e.g. 'stale data', 'missing indicators', 'degraded snapshot')."
        ),
    )
    regime_label: str | None = Field(
        default=None,
        description="Regime label this explanation is grounded in, if available",
    )
    regime_context: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Regime metadata for UI rendering. "
            "Minimum keys when available: label, family, confidence, transition, "
            "freshness, degraded_status."
        ),
    )
    generated_at: datetime = Field(..., description="Timestamp when this explanation was produced")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
