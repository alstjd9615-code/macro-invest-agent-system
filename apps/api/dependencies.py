"""FastAPI dependency providers for the analyst-facing product API.

These callables are injected into route handlers via ``Depends()`` so that
service construction is centralised, testable, and overridable in tests.

All provided services are read-only.  No write-capable services or
mutable state should be added here.

Usage::

    from apps.api.dependencies import get_macro_service, get_signal_service

    @router.get("/api/snapshots/latest")
    async def latest_snapshot(
        macro_service: MacroServiceInterface = Depends(get_macro_service),
    ) -> SnapshotLatestResponse:
        ...
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from services.interfaces import MacroServiceInterface, SignalServiceInterface
from services.macro_service import MacroService
from services.signal_service import SignalService


@lru_cache(maxsize=1)
def _macro_service_singleton() -> MacroService:
    """Return a cached :class:`~services.macro_service.MacroService` instance."""
    return MacroService()


@lru_cache(maxsize=1)
def _signal_service_singleton() -> SignalService:
    """Return a cached :class:`~services.signal_service.SignalService` instance."""
    return SignalService()


def get_macro_service() -> MacroServiceInterface:
    """FastAPI dependency: provide the macro data service.

    Returns a shared :class:`~services.macro_service.MacroService` instance.
    Override in tests with ``app.dependency_overrides[get_macro_service]``.
    """
    return _macro_service_singleton()


def get_signal_service() -> SignalServiceInterface:
    """FastAPI dependency: provide the signal evaluation service.

    Returns a shared :class:`~services.signal_service.SignalService` instance.
    Override in tests with ``app.dependency_overrides[get_signal_service]``.
    """
    return _signal_service_singleton()


# Re-export for convenience
__all__ = ["get_macro_service", "get_signal_service", "Depends"]
