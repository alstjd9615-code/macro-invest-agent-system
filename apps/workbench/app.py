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
        st.error(f"❌ Cannot connect to API at `{API_BASE_URL}`. Is the server running?")
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"❌ API error {exc.response.status_code}: {exc.response.text}")
        return None
    except Exception as exc:  # noqa: BLE001
        st.error(f"❌ Unexpected error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Layout — two-column main area
# ---------------------------------------------------------------------------

col_left, col_right = st.columns([2, 1])

# ---- Snapshot panel ----
with col_left:
    st.subheader("📈 Latest Macro Snapshot")
    with st.spinner("Fetching snapshot…"):
        snapshot_data = _get("/api/snapshots/latest", country=country)

    if snapshot_data is None:
        render_error("Could not fetch macro snapshot.")
    elif not snapshot_data.get("features"):
        render_empty("No macro features available for this country.")
    else:
        render_snapshot_panel(snapshot_data)

# ---- Signal panel ----
with col_right:
    st.subheader("🔔 Latest Signals")
    with st.spinner("Evaluating signals…"):
        signals_data = _get("/api/signals/latest", country=country)

    if signals_data is None:
        render_error("Could not fetch signal evaluations.")
    elif signals_data.get("signals_count", 0) == 0:
        render_empty("No signals generated for this country.")
    else:
        render_signal_panel(signals_data)

st.markdown("---")

# ---- Comparison panel ----
if show_comparison:
    st.subheader("🔀 Snapshot Comparison")
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
