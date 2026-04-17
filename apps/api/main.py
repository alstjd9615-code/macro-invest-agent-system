"""FastAPI application entry point for the macro-invest-agent-platform.

Exposes:
- ``GET /health``     — liveness probe: confirms the process is alive.
- ``GET /readiness``  — readiness probe: confirms core dependencies are reachable.
- ``GET /metrics``    — Prometheus metrics scrape endpoint (text/plain format).

Usage::

    uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

Environment variables are read from ``.env`` via :mod:`core.config.settings`.
"""

from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core.config.settings import get_settings
from core.tracing.tracer import configure_tracing

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="macro-invest-agent-platform",
    version="0.1.0",
    description="Macroeconomic investment agent platform — internal API.",
    docs_url="/docs",
    redoc_url=None,
)

_settings = get_settings()
configure_tracing(_settings)


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
