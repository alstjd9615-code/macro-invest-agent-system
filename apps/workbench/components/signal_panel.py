"""Signal summary panel component for the analyst workbench."""

from __future__ import annotations

from typing import Any

import streamlit as st

from apps.workbench.components.trust_badges import render_trust_badges

_SIGNAL_TYPE_ICONS = {
    "buy": "🟢 BUY",
    "sell": "🔴 SELL",
    "hold": "🟡 HOLD",
    "neutral": "⚪ NEUTRAL",
}

_TREND_ICONS = {
    "up": "↑",
    "down": "↓",
    "neutral": "→",
    "unknown": "?",
}


def render_signal_panel(data: dict[str, Any]) -> None:
    """Render signal summaries as an expandable card list.

    Args:
        data: Parsed ``SignalsLatestResponse`` JSON payload.
    """
    trust = data.get("trust", {})
    render_trust_badges(trust)

    run_id = data.get("run_id", "")
    buy = data.get("buy_count", 0)
    sell = data.get("sell_count", 0)
    hold = data.get("hold_count", 0)
    strongest = data.get("strongest_signal_id")

    st.caption(
        f"Run: `{run_id}`  ·  BUY: **{buy}**  ·  SELL: **{sell}**  ·  HOLD: **{hold}**"
        + (f"  ·  Strongest: **{strongest}**" if strongest else "")
    )

    signals = data.get("signals", [])
    if not signals:
        st.info("No signals in this run.")
        return

    for signal in signals:
        signal_id = signal.get("signal_id", "?")
        signal_type = signal.get("signal_type", "neutral")
        strength = signal.get("strength", "")
        score = signal.get("score", 0.0)
        trend = signal.get("trend", "neutral")
        rationale = signal.get("rationale", "")
        rules_passed = signal.get("rules_passed", 0)
        rules_total = signal.get("rules_total", 0)

        icon = _SIGNAL_TYPE_ICONS.get(signal_type, signal_type.upper())
        trend_icon = _TREND_ICONS.get(trend, "?")

        with st.expander(f"{icon} — `{signal_id}`  ({strength}  ·  {score:.0%})"):
            cols = st.columns(3)
            with cols[0]:
                st.metric("Type", icon)
            with cols[1]:
                st.metric("Score", f"{score:.0%}")
            with cols[2]:
                st.metric("Trend", f"{trend_icon} {trend}")

            st.progress(score)

            if rationale:
                st.markdown(f"**Rationale:** {rationale}")

            st.caption(f"Rules passed: {rules_passed} / {rules_total}")
