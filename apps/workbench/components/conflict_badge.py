"""Conflict badge component for the Macro Analyst Workbench.

Renders a colour-coded badge for the ``ConflictStatus`` of a signal or
regime explanation.  This component is explicitly separate from the
``trust_badges`` component which handles data-quality degraded badges.

Degraded (data quality problem) and Conflicted (analytical tension) must
never be conflated — they are rendered by different components in different
UI sections.

ConflictStatus → colour mapping
---------------------------------
* ``clean``          → green  🟢
* ``tension``        → amber  🟡
* ``mixed``          → red    🔴
* ``low_conviction`` → grey   ⚪
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Internal config
# ---------------------------------------------------------------------------

_CONFLICT_CONFIG: dict[str, dict[str, str]] = {
    "clean": {
        "icon": "🟢",
        "label": "Clean",
        "colour": "green",
        "description": "All macro drivers support the signal direction coherently.",
    },
    "tension": {
        "icon": "🟡",
        "label": "Tension",
        "colour": "#b8860b",  # dark amber
        "description": "Some conflicting drivers exist but supporting drivers dominate.",
    },
    "mixed": {
        "icon": "🔴",
        "label": "Mixed",
        "colour": "red",
        "description": "Conflicting and supporting drivers are roughly balanced — no clear directional view.",
    },
    "low_conviction": {
        "icon": "⚪",
        "label": "Low Conviction",
        "colour": "#888888",
        "description": "No supporting drivers or very weak quant backing — treat as indicative only.",
    },
}

_DEFAULT_CONFIG = {
    "icon": "❓",
    "label": "Unknown",
    "colour": "#888888",
    "description": "Conflict status not available.",
}


def render_conflict_badge(
    conflict_status: str,
    conflict_note: str | None = None,
    quant_support_level: str = "unknown",
    *,
    show_detail: bool = True,
) -> None:
    """Render a conflict badge for *conflict_status*.

    Displays:
    * A coloured icon + label (inline badge)
    * An optional detail tooltip / expander with the conflict_note and quant support level

    Args:
        conflict_status: One of ``clean``, ``tension``, ``mixed``, ``low_conviction``.
        conflict_note: Analyst-facing explanation of the conflict situation.
            Displayed in the detail expander when *show_detail* is ``True``.
        quant_support_level: Quant support label (strong / moderate / weak / unknown).
            Displayed alongside the conflict note.
        show_detail: When ``True``, renders an expander with the full conflict note.
    """
    cfg = _CONFLICT_CONFIG.get(conflict_status, _DEFAULT_CONFIG)
    icon = cfg["icon"]
    label = cfg["label"]
    description = cfg["description"]

    # Inline badge row
    st.markdown(
        f"**Conflict:** {icon} **{label}** &nbsp;—&nbsp; "
        f"<span style='color:{cfg['colour']};'>{description}</span>",
        unsafe_allow_html=True,
    )

    if quant_support_level and quant_support_level != "unknown":
        st.caption(f"Quant support: **{quant_support_level}**")

    if show_detail and conflict_note:
        with st.expander("Conflict detail", expanded=False):
            st.write(conflict_note)
