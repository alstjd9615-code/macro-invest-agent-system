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
* **Separated concerns**: summary and error formatting are delegated to
  :mod:`agent.formatting.summaries` and :mod:`agent.formatting.errors`
  respectively so each concern can be tested and evolved independently.

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

from agent.formatting.errors import format_signal_review_error, format_snapshot_summary_error
from agent.formatting.summaries import format_signal_review_summary, format_snapshot_summary
from agent.mcp_adapter import MCPAdapter, MCPToolError
from agent.schemas import (
    MacroSnapshotSummaryRequest,
    MacroSnapshotSummaryResponse,
    SignalReviewRequest,
    SignalReviewResponse,
)
from domain.signals.registry import SignalRegistry
from services.interfaces import MacroServiceInterface, SignalServiceInterface

_log = logging.getLogger(__name__)


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
                error_message=format_signal_review_error(
                    raw_error=exc.error_message,
                    request_id=request.request_id,
                ),
            )

        summary = format_signal_review_summary(
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
                error_message=format_snapshot_summary_error(
                    raw_error=exc.error_message,
                    request_id=request.request_id,
                    country=request.country,
                ),
                country=request.country,
            )

        summary = format_snapshot_summary(snapshot_response, request.country)
        return MacroSnapshotSummaryResponse(
            request_id=request.request_id,
            success=True,
            summary=summary,
            country=request.country,
            snapshot_timestamp=snapshot_response.snapshot_timestamp,
            features_count=snapshot_response.features_count,
        )
