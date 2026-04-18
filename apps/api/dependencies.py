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

from adapters.repositories.in_memory_macro_regime_store import InMemoryMacroRegimeStore
from adapters.repositories.in_memory_macro_snapshot_store import InMemoryMacroSnapshotStore
from services.interfaces import (
    MacroServiceInterface,
    RegimeServiceInterface,
    SignalServiceInterface,
)
from services.macro_regime_service import MacroRegimeService
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


@lru_cache(maxsize=1)
def _snapshot_store_singleton() -> InMemoryMacroSnapshotStore:
    """Return the shared in-memory snapshot store.

    Exposed so the startup seeder can write into the same instance that
    :func:`_regime_service_singleton` reads from.
    """
    return InMemoryMacroSnapshotStore()


@lru_cache(maxsize=1)
def _regime_store_singleton() -> InMemoryMacroRegimeStore:
    """Return the shared in-memory regime store."""
    return InMemoryMacroRegimeStore()


@lru_cache(maxsize=1)
def _regime_service_singleton() -> MacroRegimeService:
    """Return a cached phase-3 regime service with in-memory repositories."""
    return MacroRegimeService(
        snapshot_repository=_snapshot_store_singleton(),
        regime_repository=_regime_store_singleton(),
    )


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


def get_regime_service() -> RegimeServiceInterface:
    """FastAPI dependency: provide the regime service."""
    return _regime_service_singleton()


# Re-export for convenience
__all__ = [
    "get_macro_service",
    "get_signal_service",
    "get_regime_service",
    "get_snapshot_store",
    "Depends",
]


def get_snapshot_store() -> InMemoryMacroSnapshotStore:
    """FastAPI dependency: provide the shared snapshot store.

    Used by the startup seeder to populate the same store that the regime
    service reads from.
    """
    return _snapshot_store_singleton()
