"""Comparison table component for the analyst workbench."""

from __future__ import annotations

from typing import Any

import streamlit as st

from apps.workbench.components.trust_badges import render_trust_badges

_DIRECTION_ICONS = {
    "increased": "↑",
    "decreased": "↓",
    "unchanged": "→",
    "no_prior": "—",
}

_DIRECTION_COLORS = {
    "increased": "green",
    "decreased": "red",
    "unchanged": "gray",
    "no_prior": "gray",
}


def render_comparison_table(data: dict[str, Any]) -> None:
    """Render snapshot comparison as an annotated table.

    Args:
        data: Parsed ``SnapshotCompareResponse`` JSON payload.
    """
    trust = data.get("trust", {})
    render_trust_badges(trust)

    prior_label = data.get("prior_snapshot_label", "prior")
    changed = data.get("changed_count", 0)
    unchanged = data.get("unchanged_count", 0)
    no_prior = data.get("no_prior_count", 0)

    st.caption(
        f"Prior: **{prior_label}**  ·  "
        f"Changed: **{changed}**  ·  "
        f"Unchanged: **{unchanged}**  ·  "
        f"No prior: **{no_prior}**"
    )

    deltas = data.get("deltas", [])
    if not deltas:
        st.info("No delta records available.")
        return

    # Build display rows
    rows = []
    for delta in deltas:
        direction = delta.get("direction", "no_prior")
        icon = _DIRECTION_ICONS.get(direction, "?")
        label = delta.get("indicator_label", delta.get("indicator_type", "?"))
        current = delta.get("current_value")
        prior = delta.get("prior_value")
        d = delta.get("delta")
        rows.append(
            {
                "Indicator": label,
                "Direction": f"{icon} {direction}",
                "Current": f"{current:.4g}" if current is not None else "—",
                "Prior": f"{prior:.4g}" if prior is not None else "—",
                "Δ": f"{d:+.4g}" if d is not None else "—",
            }
        )

    st.table(rows)
