"""Thin, read-only agent service for signal review and macro snapshot summarisation.

The agent service orchestrates MCP tool calls and formats the results into
schema-validated :class:`~agent.schemas.SignalReviewResponse` or
:class:`~agent.schemas.MacroSnapshotSummaryResponse` objects.

Design principles
-----------------
* **Read-only**: the service never mutates state.
* **Deterministic**: outputs depend only on tool responses; no LLM or
  randomness is involved.
* **Thin**: no business logic lives here — domain rules stay in ``domain/``,
  data access stays in ``services/``, and tool wiring stays in ``mcp/``.
* **Error-safe**: :class:`~agent.mcp_adapter.MCPToolError` from the adapter
  is caught and converted into a failed agent response so callers never
  receive uncaught exceptions.

Usage example::

    from services.macro_service import MacroService
    from services.signal_service import SignalService
    from agent.service import AgentService
    from agent.schemas import SignalReviewRequest

    service = AgentService(MacroService(), SignalService())
    response = await service.review_signals(
        SignalReviewRequest(request_id="req-001", signal_ids=["bull_market"])
    )
    if response.success:
        print(response.summary)
"""

from __future__ import annotations

import logging

from agent.mcp_adapter import MCPAdapter, MCPToolError
from agent.schemas import (
    MacroSnapshotSummaryRequest,
    MacroSnapshotSummaryResponse,
    SignalReviewRequest,
    SignalReviewResponse,
)
from domain.signals.registry import SignalRegistry
from mcp.schemas.get_macro_features import GetMacroSnapshotResponse
from mcp.schemas.run_signal_engine import RunSignalEngineResponse
from services.interfaces import MacroServiceInterface, SignalServiceInterface

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers: deterministic summary formatters
# ---------------------------------------------------------------------------


def _format_signal_review_summary(
    response: RunSignalEngineResponse,
    signal_ids: list[str],
    country: str,
) -> str:
    """Build a deterministic one-paragraph signal review summary.

    Args:
        response: Successful MCP response from the signal engine.
        signal_ids: IDs that were reviewed.
        country: Country code used for the macro snapshot.

    Returns:
        A concise summary string describing the signal review outcome.
    """
    ids_str = ", ".join(signal_ids)
    dominance = _dominant_signal_type(response)
    return (
        f"Signal review for [{ids_str}] (country={country}): "
        f"{response.signals_generated} signal(s) generated "
        f"(BUY={response.buy_signals}, SELL={response.sell_signals}, "
        f"HOLD={response.hold_signals}). "
        f"Dominant signal direction: {dominance}. "
        f"Engine run ID: {response.engine_run_id}. "
        f"Execution time: {response.execution_time_ms:.1f}ms."
    )


def _dominant_signal_type(response: RunSignalEngineResponse) -> str:
    """Return the dominant signal type label based on counts.

    Returns the type with the highest count, breaking ties in the order
    BUY > SELL > HOLD.  Returns ``"none"`` if no signals were generated.
    """
    counts = {
        "BUY": response.buy_signals,
        "SELL": response.sell_signals,
        "HOLD": response.hold_signals,
    }
    if not any(counts.values()):
        return "none"
    return max(counts, key=lambda k: counts[k])


def _format_snapshot_summary(
    response: GetMacroSnapshotResponse,
    country: str,
) -> str:
    """Build a deterministic one-paragraph macro snapshot summary.

    Args:
        response: Successful MCP response from the snapshot tool.
        country: Country code for which the snapshot was fetched.

    Returns:
        A concise summary string describing the snapshot.
    """
    ts_str = (
        response.snapshot_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        if response.snapshot_timestamp is not None
        else "unknown"
    )
    return (
        f"Macro snapshot for country={country}: "
        f"{response.features_count} feature(s) available "
        f"as of {ts_str}."
    )


# ---------------------------------------------------------------------------
# Agent service
# ---------------------------------------------------------------------------


class AgentService:
    """Read-only agent service that orchestrates MCP tool calls.

    Provides two operations:

    * :meth:`review_signals` — run the signal engine and summarise results.
    * :meth:`summarize_macro_snapshot` — fetch and summarise the macro snapshot.

    Both operations return schema-validated response objects and never raise.

    Args:
        macro_service: Macro data service implementation.
        signal_service: Signal evaluation service implementation.
        registry: Signal definition registry.  Defaults to the built-in
            :data:`~domain.signals.registry.default_registry` when ``None``.
    """

    def __init__(
        self,
        macro_service: MacroServiceInterface,
        signal_service: SignalServiceInterface,
        registry: SignalRegistry | None = None,
    ) -> None:
        self._adapter = MCPAdapter(macro_service, signal_service, registry)

    # ------------------------------------------------------------------
    # Public operations
    # ------------------------------------------------------------------

    async def review_signals(self, request: SignalReviewRequest) -> SignalReviewResponse:
        """Review one or more signals against the current macro snapshot.

        Calls the ``run_signal_engine`` MCP tool and formats the engine output
        into a :class:`~agent.schemas.SignalReviewResponse`.

        Args:
            request: Validated :class:`~agent.schemas.SignalReviewRequest`.

        Returns:
            :class:`~agent.schemas.SignalReviewResponse` — ``success=True``
            with signal counts and a deterministic ``summary`` on success, or
            ``success=False`` with ``error_message`` on any tool failure.
        """
        try:
            engine_response = await self._adapter.run_signal_engine(
                request_id=request.request_id,
                signal_ids=request.signal_ids,
                country=request.country,
            )
        except MCPToolError as exc:
            _log.warning(
                "Signal review failed (request_id=%s): %s",
                request.request_id,
                exc,
            )
            return SignalReviewResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(exc),
            )

        summary = _format_signal_review_summary(
            engine_response, request.signal_ids, request.country
        )
        return SignalReviewResponse(
            request_id=request.request_id,
            success=True,
            summary=summary,
            engine_run_id=engine_response.engine_run_id,
            signals_generated=engine_response.signals_generated,
            buy_signals=engine_response.buy_signals,
            sell_signals=engine_response.sell_signals,
            hold_signals=engine_response.hold_signals,
            execution_time_ms=engine_response.execution_time_ms,
        )

    async def summarize_macro_snapshot(
        self,
        request: MacroSnapshotSummaryRequest,
    ) -> MacroSnapshotSummaryResponse:
        """Summarise the current macro snapshot for a given country.

        Calls the ``get_macro_snapshot`` MCP tool and formats the result into
        a :class:`~agent.schemas.MacroSnapshotSummaryResponse`.

        Args:
            request: Validated :class:`~agent.schemas.MacroSnapshotSummaryRequest`.

        Returns:
            :class:`~agent.schemas.MacroSnapshotSummaryResponse` —
            ``success=True`` with snapshot metadata and a deterministic
            ``summary`` on success, or ``success=False`` with
            ``error_message`` on any tool failure.
        """
        try:
            snapshot_response = await self._adapter.get_macro_snapshot(
                request_id=request.request_id,
                country=request.country,
            )
        except MCPToolError as exc:
            _log.warning(
                "Macro snapshot summary failed (request_id=%s): %s",
                request.request_id,
                exc,
            )
            return MacroSnapshotSummaryResponse(
                request_id=request.request_id,
                success=False,
                error_message=str(exc),
                country=request.country,
            )

        summary = _format_snapshot_summary(snapshot_response, request.country)
        return MacroSnapshotSummaryResponse(
            request_id=request.request_id,
            success=True,
            summary=summary,
            country=request.country,
            snapshot_timestamp=snapshot_response.snapshot_timestamp,
            features_count=snapshot_response.features_count,
        )
