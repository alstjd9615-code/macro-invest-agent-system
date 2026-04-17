"""FastAPI application entry point for the macro-invest-agent-platform.

Exposes:
- ``GET /health``                     — liveness probe.
- ``GET /readiness``                  — readiness probe.
- ``GET /metrics``                    — Prometheus metrics scrape endpoint.
- ``GET /api/snapshots/latest``       — latest macro snapshot (analyst read).
- ``POST /api/snapshots/compare``     — snapshot comparison (analyst read).
- ``GET /api/signals/latest``         — latest experimental signal evaluations.
- ``GET /api/regimes/latest``         — latest persisted macro regime (analyst read).
- ``GET /api/regimes/compare``        — current-vs-prior regime transition (analyst read).
- ``GET /api/explanations/{id}``      — experimental explanation by ID.
- ``GET /api/sessions/{id}``          — session context by ID (analyst read).

Usage::

    uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

Environment variables are read from ``.env`` via :mod:`core.config.settings`.
"""

from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from apps.api.routers import explanations as explanations_router
from apps.api.routers import regimes as regimes_router
from apps.api.routers import sessions as sessions_router
from apps.api.routers import signals as signals_router
from apps.api.routers import snapshots as snapshots_router
from core.config.settings import get_settings
from core.tracing.tracer import configure_tracing

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="macro-invest-agent-platform",
    version="0.1.0",
    description=(
        "Macroeconomic investment agent platform — analyst-facing read API. "
        "Provides read-only access to macro observations/snapshots and regime outputs. "
        "Signals and explanations are currently marked experimental surfaces."
    ),
    docs_url="/docs",
    redoc_url=None,
)

_settings = get_settings()
configure_tracing(_settings)

# ---------------------------------------------------------------------------
# Register analyst-facing routers
# ---------------------------------------------------------------------------

app.include_router(snapshots_router.router)
app.include_router(signals_router.router)
app.include_router(explanations_router.router)
app.include_router(sessions_router.router)
app.include_router(regimes_router.router)


# ---------------------------------------------------------------------------
# Health and readiness probes
# ---------------------------------------------------------------------------


@app.get("/health", tags=["ops"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Return ``{"status": "ok"}`` to confirm the process is alive.

    Kubernetes liveness probes should call this endpoint.  It performs no
    dependency checks — it only verifies that the application process and
    event loop are running.
    """
    return {"status": "ok"}


@app.get("/readiness", tags=["ops"], summary="Readiness probe")
async def readiness() -> dict[str, str]:
    """Return readiness status, confirming configuration is valid.

    Kubernetes readiness probes should call this endpoint.  Currently performs
    a lightweight config sanity check.  Extend this to include database or
    feature-store ping when those dependencies are required at startup.
    """
    return {"status": "ready", "env": _settings.app_env.value}


# ---------------------------------------------------------------------------
# Prometheus metrics endpoint
# ---------------------------------------------------------------------------


@app.get("/metrics", tags=["ops"], summary="Prometheus metrics scrape endpoint")
async def metrics() -> Response:
    """Expose all registered Prometheus metrics in Prometheus text format.

    Configure your Prometheus scrape job to call ``GET /metrics``.

    When ``METRICS_ENABLED=false`` the endpoint returns an empty 200 response
    so scrape jobs do not fail while metrics are disabled.
    """
    if not _settings.metrics_enabled:
        return Response(content="", media_type="text/plain")

    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
