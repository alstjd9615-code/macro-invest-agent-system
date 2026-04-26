"""Analyst workbench — main Streamlit application entry point.

Run with::

    streamlit run apps/workbench/app.py

Set the ``API_BASE_URL`` environment variable to point at the FastAPI server
(default: ``http://localhost:8000``).

Architecture
------------
* All data is fetched from the FastAPI read API — the workbench never calls
  domain services directly.
* All analyst actions are read-only; no writes or mutations are exposed.
* Trust metadata badges are prominently displayed on every panel.
"""

from __future__ import annotations

import os

import requests
import streamlit as st

from apps.workbench.components.comparison_table import render_comparison_table
from apps.workbench.components.explanation_panel import render_explanation_panel
from apps.workbench.components.regime_panel import render_regime_banner
from apps.workbench.components.signal_panel import render_signal_panel
from apps.workbench.components.snapshot_panel import render_snapshot_panel
from apps.workbench.components.states import render_empty, render_error

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Macro Analyst Workbench",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ Controls")
country = st.sidebar.text_input("Country", value="US", max_chars=2).upper()
st.sidebar.markdown("---")
show_comparison = st.sidebar.checkbox("Show comparison view", value=False)

if show_comparison:
    prior_label = st.sidebar.text_input("Prior snapshot label", value="prior")
    prior_gdp = st.sidebar.number_input("Prior GDP", value=3.0, step=0.1)
    prior_inflation = st.sidebar.number_input("Prior inflation", value=2.5, step=0.1)
    prior_unemployment = st.sidebar.number_input("Prior unemployment", value=4.0, step=0.1)
else:
    prior_label = ""
    prior_gdp = 0.0
    prior_inflation = 0.0
    prior_unemployment = 0.0

st.sidebar.markdown("---")
alerts_limit = st.sidebar.slider("Max alerts to show", min_value=3, max_value=20, value=5)
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# ---------------------------------------------------------------------------
# Main area — title
# ---------------------------------------------------------------------------

st.title("📊 Macro Analyst Workbench")
st.caption(f"Read-only analyst view  ·  API: `{API_BASE_URL}`  ·  Country: **{country}**")
st.markdown("---")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(path: str, **params: object) -> dict[str, object] | None:
    """Perform a GET request against the API; return JSON dict or None on error."""
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=10)  # type: ignore[arg-type]
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at `{API_BASE_URL}`. Is the server running?")
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"❌ API error {exc.response.status_code}: {exc.response.text}")
        return None
    except Exception as exc:  # noqa: BLE001
        st.error(f"❌ Unexpected error: {exc}")
        return None


def _post(path: str, body: dict[str, object]) -> dict[str, object] | None:
    """Perform a POST request against the API; return JSON dict or None on error."""
    try:
        resp = requests.post(f"{API_BASE_URL}{path}", json=body, timeout=10)
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to API at `{API_BASE_URL}`. Is the server running?")
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text}")
        return None
    except Exception as exc:  # noqa: BLE001
        st.error(f"Unexpected error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Section 1 — Regime Status Banner (always at the top, most important signal)
# ---------------------------------------------------------------------------

st.subheader("🏛️ Current Macro Regime")
with st.spinner("Fetching regime…"):
    regime_data = _get("/api/regimes/latest")

if regime_data is None:
    render_error("Could not fetch regime status.")
else:
    render_regime_banner(regime_data)

st.markdown("---")

# ---------------------------------------------------------------------------
# Section 2 — Three-column main view: Snapshot | Signals | Alerts
# ---------------------------------------------------------------------------

col_snapshot, col_signals, col_alerts = st.columns([3, 2, 2])

with col_snapshot:
    st.subheader("📈 Macro Indicators")
    with st.spinner("Fetching snapshot…"):
        snapshot_data = _get("/api/snapshots/latest", country=country)

    if snapshot_data is None:
        render_error("Could not fetch macro snapshot.")
    elif not snapshot_data.get("features"):
        render_empty("No macro features available for this country.")
    else:
        render_snapshot_panel(snapshot_data)

with col_signals:
    st.subheader("🔔 Signals")
    with st.spinner("Evaluating signals…"):
        signals_data = _get("/api/signals/latest", country=country)

    if signals_data is None:
        render_error("Could not fetch signals.")
    elif signals_data.get("signals_count", 0) == 0:
        render_empty("No signals generated.")
    else:
        render_signal_panel(signals_data)

with col_alerts:
    st.subheader("🚨 Recent Alerts")
    with st.spinner("Fetching alerts…"):
        alerts_data = _get("/api/alerts/recent", country=country, limit=alerts_limit)

    if alerts_data is None:
        render_error("Could not fetch alerts.")
    else:
        alerts = alerts_data.get("alerts", [])
        total = alerts_data.get("total", 0)

        if not alerts:
            render_empty("No recent alerts.")
        else:
            st.caption(f"Showing {len(alerts)} of {total} alerts")
            _SEV_ICONS = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
            for alert in alerts:
                sev = alert.get("severity", "info")
                icon = _SEV_ICONS.get(sev, "⚪")
                msg = alert.get("message", "")
                rule = alert.get("rule_name", "")
                t = alert.get("triggered_at", "")[:16].replace("T", " ")
                ack = alert.get("acknowledgement_state", "active")
                ack_badge = " ✅" if ack == "acknowledged" else ""
                with st.expander(f"{icon} {rule}{ack_badge}", expanded=sev == "critical"):
                    st.caption(f"🕐 {t}  ·  Severity: **{sev}**")
                    if msg:
                        st.write(msg)

st.markdown("---")

# ---------------------------------------------------------------------------
# Section 3 — Detail tabs: Explanation | Regime History | Comparison
# ---------------------------------------------------------------------------

tab_explain, tab_history, tab_compare = st.tabs(
    ["🧠 Explanation", "📊 Regime History", "🔀 Comparison"]
)

with tab_explain:
    with st.spinner("Fetching explanation…"):
        explanation_data = _get("/api/explanations/regime/latest")

    if explanation_data is None:
        render_error("Could not fetch regime explanation.")
    else:
        render_explanation_panel(explanation_data)

with tab_history:
    with st.spinner("Fetching regime history…"):
        history_data = _get("/api/regimes/history")
        compare_regime_data = _get("/api/regimes/compare")

    if compare_regime_data:
        delta = compare_regime_data.get("delta") or {}
        changed = compare_regime_data.get("changed", False)
        curr_label = compare_regime_data.get("current_regime_label", "—")
        prior_label_h = compare_regime_data.get("prior_regime_label", "—")
        severity = delta.get("severity", "unchanged")
        rationale_h = compare_regime_data.get("current_rationale_summary", "")

        if changed:
            label_tr = delta.get("label_transition") or f"{prior_label_h} → {curr_label}"
            st.info(f"🔄 **Regime change:** {label_tr}  ·  Severity: **{severity}**")
            notable = delta.get("notable_flags", [])
            if notable:
                st.caption("Notable flags: " + ", ".join(notable))
        else:
            st.success(f"✅ Regime **{curr_label}** is unchanged from prior period.")

        if rationale_h:
            st.markdown(f"**Current rationale:** {rationale_h}")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Current", curr_label, delta=("↑ changed" if changed else None))
        with c2:
            st.metric("Prior", prior_label_h or "—")
        with c3:
            conf_dir = delta.get("confidence_direction", "")
            conf_tr = delta.get("confidence_transition") or compare_regime_data.get("current_confidence", "—")
            st.metric("Confidence", conf_tr, delta=conf_dir if conf_dir not in ("not_applicable", "unchanged") else None)

    st.markdown("---")

    if history_data:
        regimes_list: list[dict[str, object]] = history_data.get("regimes", [])  # type: ignore[assignment]
        if regimes_list:
            st.caption(f"Recent regimes ({len(regimes_list)} entries)")
            for r in regimes_list:
                r_label = str(r.get("regime_label", "?")).upper()
                r_conf = str(r.get("confidence", "?"))
                r_date = str(r.get("as_of_date", ""))
                r_seeded = r.get("is_seeded", False)
                seed_tag = " *(seed)*" if r_seeded else ""
                st.caption(f"**{r_label}** · {r_conf} · {r_date}{seed_tag}")
        else:
            render_empty("No regime history available.")
    else:
        render_error("Could not fetch regime history.")

with tab_compare:
    if not show_comparison:
        st.info("Enable **'Show comparison view'** in the sidebar to use this tab.")
    else:
        prior_features = [
            {"indicator_type": "gdp", "value": prior_gdp},
            {"indicator_type": "inflation", "value": prior_inflation},
            {"indicator_type": "unemployment", "value": prior_unemployment},
        ]
        with st.spinner("Computing comparison…"):
            compare_data = _post(
                "/api/snapshots/compare",
                {
                    "country": country,
                    "prior_snapshot_label": prior_label or "prior",
                    "prior_features": prior_features,
                },
            )

        if compare_data is None:
            render_error("Could not fetch comparison data.")
        elif not compare_data.get("deltas"):
            render_empty("No comparison data available.")
        else:
            render_comparison_table(compare_data)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.caption("⚠️ Read-only workbench — no write actions.  Data sourced from deterministic domain layer.")
