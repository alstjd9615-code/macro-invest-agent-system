"""Trust badge components for the analyst workbench.

Renders inline Streamlit status badges for:

* Freshness (fresh / stale / unknown)
* Data availability (full / partial / degraded / unavailable)
* Source attribution
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_trust_badges(trust: dict[str, Any]) -> None:
    """Render trust metadata as compact inline badges.

    Args:
        trust: The ``trust`` dict from an API response payload.
    """
    if not trust:
        return

    freshness = trust.get("freshness_status", "unknown")
    availability = trust.get("availability", "full")
    is_degraded = trust.get("is_degraded", False)
    sources = trust.get("sources", [])
    snapshot_ts = trust.get("snapshot_timestamp")
    prev_ts = trust.get("previous_snapshot_timestamp")
    changed = trust.get("changed_indicators_count")

    cols = st.columns([1, 1, 1, 2])

    with cols[0]:
        _freshness_badge(freshness)

    with cols[1]:
        _availability_badge(availability, is_degraded)

    with cols[2]:
        if changed is not None:
            st.metric("Changed indicators", changed)

    with cols[3]:
        if sources:
            labels = [s.get("source_label", s.get("source_id", "?")) for s in sources]
            st.caption("📡 Sources: " + "  ·  ".join(labels))
        if snapshot_ts:
            st.caption(f"🕐 Snapshot: `{snapshot_ts}`")
        if prev_ts:
            st.caption(f"🕐 Prior: `{prev_ts}`")


def _freshness_badge(freshness: str) -> None:
    if freshness == "fresh":
        st.success("🟢 Fresh")
    elif freshness == "stale":
        st.warning("🟡 Stale")
    else:
        st.info("⚪ Unknown freshness")


def _availability_badge(availability: str, is_degraded: bool) -> None:
    if availability == "full":
        st.success("✅ Full data")
    elif availability == "partial":
        st.warning("🟡 Partial data")
    elif availability == "degraded" or is_degraded:
        st.warning("⚠️ Degraded")
    elif availability == "unavailable":
        st.error("❌ Unavailable")
    else:
        st.info(f"ℹ️ {availability}")
