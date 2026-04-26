"""Regime status banner component for the analyst workbench."""

from __future__ import annotations

from typing import Any

import streamlit as st

_REGIME_COLOURS: dict[str, str] = {
    "goldilocks": "🟢",
    "recovery": "🔵",
    "slowdown": "🟠",
    "stagflation": "🔴",
    "contraction": "🔴",
    "overheating": "🟠",
    "deflation": "🔵",
}

_CONFIDENCE_COLOURS: dict[str, str] = {
    "high": "🟢",
    "medium": "🟡",
    "low": "🔴",
    "unknown": "⚪",
}

_SEVERITY_LABELS: dict[str, str] = {
    "unchanged": "",
    "minor": "🔸 Minor change",
    "moderate": "🔶 Moderate change",
    "major": "🔴 Major transition",
}


def render_regime_banner(data: dict[str, Any]) -> None:
    """Render the regime status as a prominent top banner.

    Args:
        data: Parsed ``RegimeLatestResponse`` JSON payload.
    """
    label = data.get("regime_label", "unknown").upper()
    family = data.get("regime_family", "")
    confidence = data.get("confidence", "unknown").lower()
    freshness = data.get("freshness_status", "")
    degraded = data.get("degraded_status", "")
    is_seeded = data.get("is_seeded", False)
    warnings = data.get("warnings", [])
    as_of = data.get("as_of_date", "")
    rationale = data.get("rationale_summary", "")
    transition = data.get("transition", {})

    regime_icon = _REGIME_COLOURS.get(label.lower(), "⚪")
    conf_icon = _CONFIDENCE_COLOURS.get(confidence, "⚪")

    col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
    with col1:
        st.metric(
            label="Current Regime",
            value=f"{regime_icon} {label}",
            help=f"Family: {family}",
        )
    with col2:
        st.metric(label="Confidence", value=f"{conf_icon} {confidence.upper()}")
    with col3:
        st.metric(label="Freshness", value=freshness.upper() if freshness else "—")
    with col4:
        st.metric(label="As of Date", value=str(as_of))

    # Transition badge
    t_type = transition.get("transition_type", "")
    t_changed = transition.get("changed", False)
    if t_changed and t_type:
        st.info(f"🔄 **Regime transition detected** — {t_type.replace('_', ' ').title()}")
    elif t_type:
        st.caption(f"Transition: {t_type.replace('_', ' ')}")

    # Rationale summary
    if rationale:
        with st.expander("📝 Regime rationale", expanded=False):
            st.write(rationale)

    # Warnings
    if is_seeded:
        st.warning("⚠️ **Bootstrap mode** — regime derived from synthetic seed data, not live ingestion.")

    for w in warnings:
        if w:
            st.warning(f"⚠️ {w}")

    if degraded and degraded not in ("none", "clean", ""):
        st.error(f"🔴 Degraded status: **{degraded}**")
