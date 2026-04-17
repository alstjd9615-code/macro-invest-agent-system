"""Snapshot summary panel component for the analyst workbench."""

from __future__ import annotations

from typing import Any

import streamlit as st

from apps.workbench.components.trust_badges import render_trust_badges


def render_snapshot_panel(data: dict[str, Any]) -> None:
    """Render the latest macro snapshot as a labelled metric grid.

    Args:
        data: Parsed ``SnapshotLatestResponse`` JSON payload.
    """
    trust = data.get("trust", {})
    render_trust_badges(trust)

    features = data.get("features", [])
    if not features:
        st.info("No features in this snapshot.")
        return

    # Render features in a 3-column grid
    cols_per_row = 3
    for i in range(0, len(features), cols_per_row):
        row = features[i : i + cols_per_row]
        cols = st.columns(len(row))
        for col, feature in zip(cols, row, strict=False):
            with col:
                label = feature.get("indicator_label", feature.get("indicator_type", "?"))
                value = feature.get("value", 0.0)
                source = feature.get("source_id", "")
                freq = feature.get("frequency", "")
                st.metric(
                    label=label,
                    value=f"{value:.4g}",
                    help=f"Source: {source}  ·  Frequency: {freq}",
                )
