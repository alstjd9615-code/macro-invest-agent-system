"""Loading, empty, and error state components for the analyst workbench.

These helpers provide consistent UX states across all workbench panels.
"""

from __future__ import annotations

import streamlit as st


def render_loading(message: str = "Loading…") -> None:
    """Display a spinner with an optional message.

    Args:
        message: Text to show beside the spinner.
    """
    with st.spinner(message):
        pass


def render_empty(message: str = "No data available.") -> None:
    """Display a neutral empty-state message.

    Args:
        message: Text to show in the empty state.
    """
    st.info(f"ℹ️ {message}")


def render_error(message: str = "An error occurred.") -> None:
    """Display a prominent error state.

    Args:
        message: Error description to display.
    """
    st.error(f"❌ {message}")
