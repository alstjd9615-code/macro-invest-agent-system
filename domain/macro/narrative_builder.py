"""Analyst-facing regime narrative builder.

Generates structured, human-readable narratives from a
:class:`~domain.macro.regime.MacroRegime`.  The output is designed to be
surfaced directly to analysts via the explanation API.

Design principles
-----------------
* Narratives must be **analyst-facing**, not debug traces.
* Every field must be explainable in plain English.
* The builder is deterministic: the same regime always produces the same
  narrative.
* Empty-state, degraded-state, stale-state, and error-state produce
  explicitly different summary text.
"""

from __future__ import annotations

from datetime import UTC, datetime

from domain.macro.regime import MacroRegime, RegimeConfidence, RegimeLabel
from domain.macro.snapshot import DegradedStatus
from pipelines.ingestion.models import FreshnessStatus

# ---------------------------------------------------------------------------
# Narrative templates per regime label
# ---------------------------------------------------------------------------

_LABEL_SUMMARY: dict[RegimeLabel, str] = {
    RegimeLabel.GOLDILOCKS: (
        "The macro environment is in a Goldilocks regime: growth is accelerating, "
        "inflation is cooling, and monetary policy is broadly neutral. "
        "This is the most favourable backdrop for risk assets."
    ),
    RegimeLabel.DISINFLATION: (
        "A Disinflation regime is underway: inflation is retreating while growth "
        "remains mixed or slowing. Rate pressure is easing, benefiting duration assets, "
        "but growth momentum is insufficient to strongly support equities."
    ),
    RegimeLabel.REFLATION: (
        "A Reflation regime is emerging: inflation is re-accelerating alongside "
        "improving growth and accommodative policy. This supports cyclical assets, "
        "commodities, and inflation-linked instruments while pressuring nominal bonds."
    ),
    RegimeLabel.SLOWDOWN: (
        "A Slowdown regime is in effect: growth is decelerating and the labour market "
        "is softening. The risk of a further growth deterioration is elevated. "
        "Defensive positioning and duration extension are favoured."
    ),
    RegimeLabel.STAGFLATION_RISK: (
        "Stagflation risk is elevated: growth is slowing while inflation is re-accelerating "
        "and the labour market is weakening. This is the most challenging regime for "
        "traditional portfolios — both equities and bonds face headwinds."
    ),
    RegimeLabel.CONTRACTION: (
        "A Contraction regime has been identified: broad growth is contracting, "
        "financial conditions are tight, and the labour market is weak. "
        "Maximum risk-off posture is warranted; flight to quality and duration extension "
        "are appropriate."
    ),
    RegimeLabel.POLICY_TIGHTENING_DRAG: (
        "Policy Tightening Drag is the prevailing regime: restrictive monetary policy "
        "and tight financial conditions are weighing on growth. "
        "Multiples are compressed; avoid extending duration or adding cyclical risk "
        "until a policy pivot is confirmed."
    ),
    RegimeLabel.MIXED: (
        "Mixed macro signals are preventing a clear regime classification. "
        "Opposing forces across growth, inflation, labour, and financial conditions "
        "reduce the reliability of any directional call. "
        "Maintain a balanced, diversified allocation until the picture clarifies."
    ),
    RegimeLabel.UNCLEAR: (
        "The macro regime is unclear. Insufficient or stale data is preventing reliable "
        "classification. No high-conviction signal can be derived from the current "
        "macro state. Refresh data sources and re-evaluate before acting."
    ),
}

_CONFIDENCE_NARRATIVE: dict[RegimeConfidence, str] = {
    RegimeConfidence.HIGH: "Regime confidence is HIGH — all key indicators are fresh and non-conflicting.",
    RegimeConfidence.MEDIUM: (
        "Regime confidence is MEDIUM — some indicators are late or partially missing, "
        "introducing moderate uncertainty."
    ),
    RegimeConfidence.LOW: (
        "Regime confidence is LOW — significant data gaps, staleness, or conflicting "
        "signals reduce the reliability of this classification."
    ),
}

_FRESHNESS_NOTE: dict[FreshnessStatus, str] = {
    FreshnessStatus.FRESH: "All underlying data is fresh.",
    FreshnessStatus.LATE: "Some underlying data is late; results may not reflect the latest releases.",
    FreshnessStatus.STALE: "Underlying data is stale; this regime classification may be outdated.",
    FreshnessStatus.UNKNOWN: "Data freshness is unknown; treat this regime with caution.",
}

_DEGRADED_NOTE: dict[DegradedStatus, str] = {
    DegradedStatus.NONE: "",
    DegradedStatus.PARTIAL: "Some indicators are missing; the regime is derived from partial data.",
    DegradedStatus.MISSING: "Critical indicators are missing; this regime is derived from a degraded snapshot.",
    DegradedStatus.SOURCE_UNAVAILABLE: (
        "Data source is unavailable; the regime reflects the last available snapshot only."
    ),
    DegradedStatus.UNKNOWN: "Degraded status is unknown.",
}

_STATE_LABELS: dict[str, str] = {
    "growth_state": "Growth",
    "inflation_state": "Inflation",
    "labor_state": "Labour",
    "policy_state": "Policy",
    "financial_conditions_state": "Financial Conditions",
}


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------


def build_regime_narrative(regime: MacroRegime) -> dict[str, object]:
    """Build an analyst-facing narrative for *regime*.

    Returns a dict with the following keys:

    * ``summary`` — a concise multi-sentence interpretation of the regime.
    * ``rationale_points`` — ordered list of supporting bullet points.
    * ``regime_label`` — the string value of the regime label.
    * ``regime_context`` — dict of contextual metadata for UI rendering.
    * ``generated_at`` — ISO 8601 UTC timestamp when this narrative was built.

    Args:
        regime: The :class:`~domain.macro.regime.MacroRegime` to narrate.

    Returns:
        Dict conforming to the fields expected by
        :class:`~apps.api.dto.explanations.ExplanationResponse`.
    """
    summary_lines: list[str] = []

    # Core regime interpretation
    label_text = _LABEL_SUMMARY.get(regime.regime_label, _LABEL_SUMMARY[RegimeLabel.UNCLEAR])
    summary_lines.append(label_text)

    # Confidence sentence
    confidence_text = _CONFIDENCE_NARRATIVE.get(
        regime.confidence, _CONFIDENCE_NARRATIVE[RegimeConfidence.LOW]
    )
    summary_lines.append(confidence_text)

    # Degraded / freshness caveats
    degraded_note = _DEGRADED_NOTE.get(regime.degraded_status, "")
    if degraded_note:
        summary_lines.append(degraded_note)
    else:
        freshness_note = _FRESHNESS_NOTE.get(regime.freshness_status, "")
        if freshness_note:
            summary_lines.append(freshness_note)

    summary = " ".join(summary_lines)

    # Rationale bullet points
    rationale_points: list[str] = []

    # Regime identification
    rationale_points.append(
        f"Regime: {regime.regime_label.value} (family: {regime.regime_family.value})"
    )
    rationale_points.append(f"As of date: {regime.as_of_date.isoformat()}")

    # Supporting states
    for state_key, state_label in _STATE_LABELS.items():
        state_value = regime.supporting_states.get(state_key, "unknown")
        rationale_points.append(f"{state_label}: {state_value}")

    # Confidence and data quality
    rationale_points.append(f"Confidence: {regime.confidence.value}")
    if regime.freshness_status != FreshnessStatus.FRESH:
        rationale_points.append(f"Freshness: {regime.freshness_status.value}")
    if regime.degraded_status not in {DegradedStatus.NONE, DegradedStatus.UNKNOWN}:
        rationale_points.append(f"Data quality: {regime.degraded_status.value}")
    if regime.missing_inputs:
        rationale_points.append(f"Missing inputs: {', '.join(regime.missing_inputs)}")

    # Transition
    if regime.transition.transition_from_prior is not None:
        rationale_points.append(
            f"Transition from prior: {regime.transition.transition_from_prior} "
            f"({regime.transition.transition_type.value})"
        )
    else:
        rationale_points.append(f"Transition: {regime.transition.transition_type.value}")

    # Regime context for UI
    regime_context: dict[str, str] = {
        "regime_id": regime.regime_id,
        "regime_label": regime.regime_label.value,
        "regime_family": regime.regime_family.value,
        "confidence": regime.confidence.value,
        "freshness_status": regime.freshness_status.value,
        "degraded_status": regime.degraded_status.value,
        "supporting_snapshot_id": regime.supporting_snapshot_id,
        "transition_type": regime.transition.transition_type.value,
        "transition_from_prior": regime.transition.transition_from_prior or "",
    }

    return {
        "summary": summary,
        "rationale_points": rationale_points,
        "regime_label": regime.regime_label.value,
        "regime_context": regime_context,
        "generated_at": datetime.now(UTC).isoformat(),
    }
