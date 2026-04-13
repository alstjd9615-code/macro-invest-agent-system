"""MCP tool handler for signal engine execution.

Translates a :class:`~mcp.schemas.run_signal_engine.RunSignalEngineRequest`
into a coordinated sequence of service calls:

1. Resolve signal IDs → :class:`~domain.signals.models.SignalDefinition` objects
   via the :class:`~domain.signals.registry.SignalRegistry`.
2. Fetch the current macro snapshot via
   :class:`~services.interfaces.MacroServiceInterface`.
3. Run the signal engine via
   :class:`~services.interfaces.SignalServiceInterface`.
4. Return a structured :class:`~mcp.schemas.run_signal_engine.RunSignalEngineResponse`.

Callable boundary contract
---------------------------
* The handler is **async** to match the async service interface.
* The handler **never raises**; all errors are captured and returned as
  ``MCPResponse(success=False, error_message=…)``.
* The handler is **read-only**: it queries data but does not mutate state.
"""

from __future__ import annotations

import asyncio
import logging
import time

from domain.signals.enums import SignalType
from domain.signals.registry import SignalRegistry, default_registry
from mcp.schemas.run_signal_engine import RunSignalEngineRequest, RunSignalEngineResponse
from services.interfaces import MacroServiceInterface, SignalServiceInterface

_log = logging.getLogger(__name__)

# Sentinel returned in error responses where no run ID was generated.
_NO_RUN_ID = ""


async def handle_run_signal_engine(
    request: RunSignalEngineRequest,
    macro_service: MacroServiceInterface,
    signal_service: SignalServiceInterface,
    registry: SignalRegistry | None = None,
) -> RunSignalEngineResponse:
    """Execute the ``run_signal_engine`` MCP tool.

    Resolves the requested signal IDs against *registry*, fetches the macro
    snapshot for ``request.country``, and runs the signal engine.  Execution
    time is measured in milliseconds and included in the response.

    Args:
        request: Validated :class:`~mcp.schemas.run_signal_engine.RunSignalEngineRequest`.
        macro_service: Macro data service for snapshot retrieval.
        signal_service: Signal evaluation service.
        registry: Signal definition registry.  Defaults to
            :data:`~domain.signals.registry.default_registry` when ``None``.

    Returns:
        :class:`~mcp.schemas.run_signal_engine.RunSignalEngineResponse` —
        ``success=True`` with signal counts and ``engine_run_id`` on success,
        or ``success=False`` with ``error_message`` on failure.
    """
    if registry is None:
        registry = default_registry

    # ------------------------------------------------------------------
    # 1. Validate that the request contains at least one signal ID.
    # ------------------------------------------------------------------
    if not request.signal_ids:
        return RunSignalEngineResponse(
            request_id=request.request_id,
            engine_run_id=_NO_RUN_ID,
            success=False,
            error_message="signal_ids must not be empty.",
        )

    # ------------------------------------------------------------------
    # 1b. Reject use_latest_snapshot=False until the alternate path is
    #     implemented: always fetch a live snapshot for now.
    # ------------------------------------------------------------------
    if not request.use_latest_snapshot:
        return RunSignalEngineResponse(
            request_id=request.request_id,
            engine_run_id=_NO_RUN_ID,
            success=False,
            error_message=(
                "use_latest_snapshot=False is not yet supported; "
                "only live snapshot fetching is available."
            ),
        )

    # ------------------------------------------------------------------
    # 2. Resolve signal IDs → SignalDefinition objects.
    # ------------------------------------------------------------------
    signal_definitions = []
    unknown_ids: list[str] = []

    for signal_id in request.signal_ids:
        try:
            signal_definitions.append(registry.get(signal_id))
        except KeyError:
            unknown_ids.append(signal_id)

    if unknown_ids:
        joined = ", ".join(f"'{sid}'" for sid in unknown_ids)
        return RunSignalEngineResponse(
            request_id=request.request_id,
            engine_run_id=_NO_RUN_ID,
            success=False,
            error_message=f"Unknown signal ID(s): {joined}.",
        )

    # ------------------------------------------------------------------
    # 3. Fetch the macro snapshot.
    # ------------------------------------------------------------------
    try:
        snapshot = await macro_service.get_snapshot(country=request.country)
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001
        _log.exception(
            "Unexpected error fetching macro snapshot (request_id=%s)",
            request.request_id,
        )
        return RunSignalEngineResponse(
            request_id=request.request_id,
            engine_run_id=_NO_RUN_ID,
            success=False,
            error_message="Failed to fetch macro snapshot.",
        )

    # ------------------------------------------------------------------
    # 4. Run the signal engine and measure wall-clock execution time.
    # ------------------------------------------------------------------
    start = time.perf_counter()
    try:
        result = await signal_service.run_engine(signal_definitions, snapshot)
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001
        _log.exception(
            "Unexpected error running signal engine (request_id=%s)",
            request.request_id,
        )
        return RunSignalEngineResponse(
            request_id=request.request_id,
            engine_run_id=_NO_RUN_ID,
            success=False,
            error_message="Signal engine execution failed.",
        )
    execution_ms = (time.perf_counter() - start) * 1000.0

    return RunSignalEngineResponse(
        request_id=request.request_id,
        engine_run_id=result.run_id,
        success=True,
        signals_generated=len(result.signals),
        buy_signals=len(result.get_signals_by_type(SignalType.BUY)),
        sell_signals=len(result.get_signals_by_type(SignalType.SELL)),
        hold_signals=len(result.get_signals_by_type(SignalType.HOLD)),
        execution_time_ms=round(execution_ms, 3),
    )
