"""Explanation DTOs for the analyst-facing read API.

These models are the stable, frontend-friendly contracts for:

* ``GET /api/explanations/{id}`` — retrieve the explanation associated with a
  signal run or snapshot context.
* ``GET /api/explanations/regime/latest`` — analyst narrative for the current regime.
* ``GET /api/explanations/run/{run_id}`` — all explanations for a run.

Design notes
------------
* An ``Explanation`` links a human-readable ``summary`` to the specific
  ``run_id`` or ``snapshot_context_id`` that generated it.
* ``rationale_points`` is a structured list for rendering bullet points in
  the workbench explanation panel.
* ``reasoning_chain`` is the structured analyst workflow — 6 ordered reasoning
  steps that surface the full analyst decision chain: current_state → why →
  confidence → conflict → caveats → what_changed.
* ``analyst_workflow`` wraps the same steps in a typed container for UI rendering.
* Trust metadata is included so stale or degraded explanations are visibly
  surfaced in the UI.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from apps.api.dto.trust import TrustMetadata

# ---------------------------------------------------------------------------
# Reasoning / workflow primitives (Explanation Engine v2)
# ---------------------------------------------------------------------------

REASONING_STEP_KEYS = (
    "current_state",
    "why",
    "confidence",
    "conflict",
    "caveats",
    "what_changed",
)
"""Canonical ordering of the 6 analyst workflow steps.

``current_state``
    The current macro regime label and family.
``why``
    The key macro states that drove this classification.
``confidence``
    The confidence level and the rules that determined it.
``conflict``
    The conflict / conviction status and any analytical tension notes.
``caveats``
    Interpretation limits — e.g. low confidence, initial regime, missing inputs.
``what_changed``
    What changed versus the prior regime — transition type and prior label.
"""


class ReasoningStep(BaseModel, extra="forbid"):
    """A single step in the analyst reasoning chain.

    Attributes:
        step: 1-based ordinal position in the chain.
        key: Machine-readable step identifier (one of ``REASONING_STEP_KEYS``).
        label: Human-readable display label for UI rendering.
        value: Short, scannable value string (e.g. ``"goldilocks"``).
        detail: Longer analyst-facing explanation; ``None`` when not applicable.
    """

    step: int = Field(..., ge=1, description="1-based ordinal position in the reasoning chain")
    key: str = Field(
        ...,
        description=(
            "Machine-readable step key. "
            "One of: current_state, why, confidence, conflict, caveats, what_changed."
        ),
    )
    label: str = Field(..., description="Human-readable display label")
    value: str = Field(..., description="Short scannable value string")
    detail: str | None = Field(
        default=None,
        description="Longer analyst-facing explanation; None when not applicable",
    )


class WhatChangedDTO(BaseModel, extra="forbid"):
    """Structured summary of what changed vs the prior regime.

    Attributes:
        prior_regime_label: Prior regime label; ``None`` for initial regimes.
        transition_type: Transition classification (shift / unchanged / initial / etc.).
        changed: True when the regime label changed from the prior.
        changed_indicators_count: Number of snapshot indicators that changed;
            ``None`` when not available.
    """

    prior_regime_label: str | None = Field(
        default=None,
        description="Prior regime label; None for initial (no baseline) regimes",
    )
    transition_type: str = Field(
        default="initial",
        description="Transition classification: initial | unchanged | shift | weakening | strengthening",
    )
    changed: bool = Field(
        default=False,
        description="True when the regime label changed from the prior",
    )
    changed_indicators_count: int | None = Field(
        default=None,
        description="Number of snapshot indicators that changed; None when not available",
    )


class AnalystWorkflowDTO(BaseModel, extra="forbid"):
    """6-step analyst workflow surface, ready for UI rendering.

    This is a typed container for the reasoning chain that the workbench and
    any API consumer can use to render the full analyst decision workflow in
    the canonical order:
    current_state → why → confidence → conflict → caveats → what_changed.

    Attributes:
        steps: Ordered list of :class:`ReasoningStep` objects.
            Always contains exactly 6 steps when fully populated.
    """

    steps: list[ReasoningStep] = Field(
        default_factory=list,
        description="Ordered list of reasoning steps in analyst workflow order",
    )


# ---------------------------------------------------------------------------
# Explanation response contract
# ---------------------------------------------------------------------------


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

        reasoning_chain: Ordered list of :class:`ReasoningStep` objects representing
            the full analyst reasoning workflow (Explanation Engine v2).
            Contains 6 steps when fully populated by the regime explanation builder.
            May be empty for legacy in-memory signal-level explanations.
        what_changed: Structured summary of what changed vs the prior regime.
            ``None`` when no prior regime is available (initial regime).
        analyst_workflow: Typed container wrapping the reasoning chain for UI rendering.
            The ``steps`` field mirrors ``reasoning_chain``.
        conflict_status: Conflict/conviction status from the grounding signal or regime
            conflict surface. One of: ``clean`` | ``tension`` | ``mixed`` | ``low_conviction``.
        conflict_note: Analyst-facing explanation of the conflict situation.
            ``None`` when ``conflict_status`` is ``clean``.
        quant_support_level: Quant support level derived from the grounding regime's
            ``QuantScoreBundle.overall_support``. One of: ``strong`` | ``moderate`` |
            ``weak`` | ``unknown``.
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
    # ------------------------------------------------------------------
    # Explanation Engine v2 fields
    # ------------------------------------------------------------------
    reasoning_chain: list[ReasoningStep] = Field(
        default_factory=list,
        description=(
            "Structured analyst reasoning chain (Explanation Engine v2). "
            "Ordered list of 6 steps: current_state, why, confidence, conflict, "
            "caveats, what_changed. Empty for legacy signal-level explanations."
        ),
    )
    what_changed: WhatChangedDTO | None = Field(
        default=None,
        description=(
            "Structured summary of what changed vs the prior regime. "
            "None when no prior regime is available (initial regime)."
        ),
    )
    analyst_workflow: AnalystWorkflowDTO = Field(
        default_factory=AnalystWorkflowDTO,
        description=(
            "Typed 6-step analyst workflow surface for UI rendering. "
            "steps mirrors reasoning_chain. "
            "Populated for regime-level explanations."
        ),
    )
    conflict_status: str = Field(
        default="clean",
        description=(
            "Conflict/conviction status from the grounding signal or regime. "
            "One of: clean | tension | mixed | low_conviction. "
            "Distinct from trust.is_degraded — reflects analytical tension, "
            "not data quality."
        ),
    )
    conflict_note: str | None = Field(
        default=None,
        description=(
            "Analyst-facing explanation of the conflict situation. "
            "None when conflict_status is 'clean'."
        ),
    )
    quant_support_level: str = Field(
        default="unknown",
        description=(
            "Quant support level: strong | moderate | weak | unknown. "
            "Derived from QuantScoreBundle.overall_support."
        ),
    )
    generated_at: datetime = Field(..., description="Timestamp when this explanation was produced")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
