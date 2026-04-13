"""MCP tool handlers for macro feature retrieval.

These thin handler functions translate MCP request objects into service-layer
calls and map the results (or exceptions) back into structured MCP responses.
They contain no business logic: validation lives in the request schema and
domain models; data access lives in the service layer.

Callable boundary contract
---------------------------
* Handlers are **async** to match the async service interface.
* Handlers **never raise**; all errors are captured and returned as
  ``MCPResponse(success=False, error_message=…)``.
* Handlers are **read-only**: they query data but do not mutate state.
"""

from __future__ import annotations

from mcp.schemas.get_macro_features import (
    GetMacroFeaturesRequest,
    GetMacroFeaturesResponse,
    GetMacroSnapshotRequest,
    GetMacroSnapshotResponse,
)
from services.interfaces import MacroServiceInterface


async def handle_get_macro_features(
    request: GetMacroFeaturesRequest,
    service: MacroServiceInterface,
) -> GetMacroFeaturesResponse:
    """Execute the ``get_macro_features`` MCP tool.

    Fetches the requested macro indicators via *service* and returns a
    response containing the count of features retrieved.

    Args:
        request: Validated :class:`~mcp.schemas.get_macro_features.GetMacroFeaturesRequest`.
        service: Macro data service implementation.

    Returns:
        :class:`~mcp.schemas.get_macro_features.GetMacroFeaturesResponse` —
        ``success=True`` with ``features_count`` on success, or
        ``success=False`` with ``error_message`` on failure.
    """
    if not request.indicator_types:
        return GetMacroFeaturesResponse(
            request_id=request.request_id,
            success=False,
            error_message="indicator_types must not be empty.",
            features_count=0,
        )

    try:
        features = await service.fetch_features(
            indicator_types=request.indicator_types,
            country=request.country,
        )
    except ValueError as exc:
        return GetMacroFeaturesResponse(
            request_id=request.request_id,
            success=False,
            error_message=str(exc),
            features_count=0,
        )
    except Exception as exc:  # noqa: BLE001
        return GetMacroFeaturesResponse(
            request_id=request.request_id,
            success=False,
            error_message=f"Failed to fetch features: {exc}",
            features_count=0,
        )

    return GetMacroFeaturesResponse(
        request_id=request.request_id,
        success=True,
        features_count=len(features),
    )


async def handle_get_macro_snapshot(
    request: GetMacroSnapshotRequest,
    service: MacroServiceInterface,
) -> GetMacroSnapshotResponse:
    """Execute the ``get_macro_snapshot`` MCP tool.

    Retrieves a complete macro snapshot for the requested country via *service*.

    Args:
        request: Validated :class:`~mcp.schemas.get_macro_features.GetMacroSnapshotRequest`.
        service: Macro data service implementation.

    Returns:
        :class:`~mcp.schemas.get_macro_features.GetMacroSnapshotResponse` —
        ``success=True`` with snapshot metadata on success, or
        ``success=False`` with ``error_message`` on failure.
    """
    try:
        snapshot = await service.get_snapshot(country=request.country)
    except Exception as exc:  # noqa: BLE001
        return GetMacroSnapshotResponse(
            request_id=request.request_id,
            success=False,
            error_message=f"Failed to fetch snapshot: {exc}",
            snapshot_timestamp=None,
            features_count=0,
        )

    return GetMacroSnapshotResponse(
        request_id=request.request_id,
        success=True,
        snapshot_timestamp=snapshot.snapshot_time,
        features_count=len(snapshot.features),
    )
