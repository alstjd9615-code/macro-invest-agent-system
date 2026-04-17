"""Analyst workbench — Streamlit visual surface for the macro-invest platform.

This package provides a minimal, read-only visual workbench for internal analyst
usage.  It consumes the FastAPI analyst API and renders:

- Latest macro snapshot summary panel
- Snapshot comparison table / card list
- Signal summary panel
- Explanation panel
- Freshness, source, and degraded-state badges
- Loading, empty, and error states

Usage::

    streamlit run apps/workbench/app.py

The ``API_BASE_URL`` environment variable controls the target API URL
(default: ``http://localhost:8000``).
"""
