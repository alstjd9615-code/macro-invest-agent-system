"""Explanation panel component for the Macro Analyst Workbench.

Renders the v2 structured explanation for a regime or signal, following the
canonical 6-step analyst workflow:

  current_state → why → confidence → conflict → caveats → what_changed

Each step is rendered as a labelled card with a scannable value and optional
detail text.  Data-quality notes are rendered separately from conflict notes
to preserve the degraded-vs-conflicted semantic distinction.
"""

from __future__ import annotations

import streamlit as st

from apps.workbench.components.conflict_badge import render_conflict_badge

# ---------------------------------------------------------------------------
# Step icon map
# ---------------------------------------------------------------------------

_STEP_ICONS: dict[str, str] = {
    "current_state": "📍",
    "why": "🔍",
    "confidence": "🎯",
    "conflict": "⚡",
    "caveats": "⚠️",
    "what_changed": "🔄",
}

_DEFAULT_ICON = "•"


def render_explanation_panel(explanation_data: dict[str, object]) -> None:
    """Render the structured explanation panel from an :class:`ExplanationResponse` dict.

    Renders:
    1. Summary paragraph
    2. 6-step reasoning chain (analyst workflow)
    3. Conflict badge (separate from degraded trust badges)
    4. Caveats (interpretation limits)
    5. Data quality notes (freshness/degraded warnings)
    6. Rationale bullet points (expanded view)

    Args:
        explanation_data: JSON-deserialized ``ExplanationResponse`` dict from the
            ``GET /api/explanations/regime/latest`` endpoint.
    """
    if not explanation_data:
        st.info("No explanation available.")
        return

    # ---- Summary ----
    summary = explanation_data.get("summary", "")
    if summary:
        st.markdown(f"> {summary}")
        st.markdown("")

    # ---- 6-step reasoning chain ----
    analyst_workflow = explanation_data.get("analyst_workflow") or {}
    reasoning_steps = analyst_workflow.get("steps") or explanation_data.get("reasoning_chain") or []

    if reasoning_steps:
        st.markdown("**Analyst Workflow**")
        cols = st.columns(3)
        for i, step in enumerate(reasoning_steps):
            key = step.get("key", "")
            icon = _STEP_ICONS.get(key, _DEFAULT_ICON)
            label = step.get("label", key.replace("_", " ").title())
            value = step.get("value", "—")
            detail = step.get("detail")

            with cols[i % 3]:
                st.markdown(f"{icon} **{label}**")
                st.markdown(f"`{value}`")
                if detail:
                    with st.expander("Detail", expanded=False):
                        st.caption(detail)
        st.markdown("")

    # ---- Conflict badge ----
    conflict_status = str(explanation_data.get("conflict_status", "clean"))
    conflict_note = explanation_data.get("conflict_note")
    quant_support = str(explanation_data.get("quant_support_level", "unknown"))

    if conflict_status != "clean" or quant_support != "unknown":
        st.markdown("---")
        render_conflict_badge(
            conflict_status=conflict_status,
            conflict_note=str(conflict_note) if conflict_note else None,
            quant_support_level=quant_support,
        )

    # ---- Caveats ----
    caveats: list[str] = list(explanation_data.get("caveats") or [])  # type: ignore[arg-type]
    if caveats:
        st.markdown("---")
        st.markdown("**⚠️ Interpretation Caveats**")
        for caveat in caveats:
            st.warning(caveat)

    # ---- Data quality notes ----
    dq_notes: list[str] = list(explanation_data.get("data_quality_notes") or [])  # type: ignore[arg-type]
    if dq_notes:
        st.markdown("---")
        st.markdown("**🔬 Data Quality Notes**")
        for note in dq_notes:
            st.info(note)

    # ---- Rationale bullet points (collapsible) ----
    rationale_points: list[str] = list(explanation_data.get("rationale_points") or [])  # type: ignore[arg-type]
    if rationale_points:
        with st.expander("📋 Full Rationale", expanded=False):
            for point in rationale_points:
                st.markdown(f"- {point}")
