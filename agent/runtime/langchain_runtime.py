"""LangChain-wired agent runtime.

This module provides :class:`LangChainAgentRuntime` — a runtime adapter that
wraps the existing :class:`~agent.service.AgentService` with LangChain prompt
templates, tool bindings, and output schema validation.

Architecture
------------
::

    Caller
      │
      │  AgentRequest
      ▼
    ┌──────────────────────────┐
    │  LangChainAgentRuntime   │ ← prompt templates + validation
    └───────────┬──────────────┘
                │
                ▼
    ┌──────────────────────────┐
    │     AgentService         │ ← unchanged
    └───────────┬──────────────┘
                │
                ▼
    ┌──────────────────────────┐
    │     MCPAdapter           │ ← unchanged
    └───────────┬──────────────┘
                │
                ▼
          MCP Tool Handlers

Design constraints
------------------
* **Read-only**: the runtime only dispatches to read-only service methods.
* **No LLM calls**: prompt templates are rendered directly; no model is invoked.
* **Deterministic**: prompts never override or reinterpret tool results.
* **Schema-safe**: every output is validated at the boundary before return.
* **Backward-compatible**: the runtime exposes the same ``invoke`` interface
  as :class:`~agent.runtime.agent_runtime.AgentRuntime`.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from agent.formatting.summaries import dominant_signal_type
from agent.mcp_adapter import MCPAdapter
from agent.prompts.templates import render_signal_review_summary, render_snapshot_summary
from agent.runtime.agent_runtime import (
    AgentOperation,
    AgentRequestInput,
    AgentRuntimeResult,
)
from agent.runtime.output_validation import validate_runtime_result
from agent.schemas import (
    MacroSnapshotSummaryRequest,
    MacroSnapshotSummaryResponse,
    SignalReviewRequest,
    SignalReviewResponse,
)
from agent.service import AgentService

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory conversation context (optional stretch scope)
# ---------------------------------------------------------------------------

_DEFAULT_MAX_TURNS = 10


class ConversationTurn(BaseModel, extra="forbid"):
    """A single turn in the session-scoped conversation context.

    Attributes:
        request_type: The class name of the agent request.
        request_snapshot: Serialised request data for reference.
        response_summary: The ``summary`` field from the agent response.
        success: Whether the operation succeeded.
    """

    request_type: str = Field(..., description="Agent request class name")
    request_snapshot: dict[str, Any] = Field(..., description="Serialised request data")
    response_summary: str = Field(default="", description="Summary from the agent response")
    success: bool = Field(default=True, description="Whether the operation succeeded")


class ConversationContext:
    """Session-scoped, in-memory conversation context for recent-turn carryover.

    Stores up to ``max_turns`` recent turns.  No database, no persistence
    across process restarts, and no retrieval memory.

    Args:
        max_turns: Maximum number of turns to retain (FIFO eviction).
    """

    def __init__(self, max_turns: int = _DEFAULT_MAX_TURNS) -> None:
        self._turns: deque[ConversationTurn] = deque(maxlen=max_turns)

    def add_turn(self, turn: ConversationTurn) -> None:
        """Append a turn; oldest turns are evicted when the limit is reached."""
        self._turns.append(turn)

    @property
    def turns(self) -> list[ConversationTurn]:
        """Return all stored turns in chronological order."""
        return list(self._turns)

    @property
    def turn_count(self) -> int:
        """Return the number of stored turns."""
        return len(self._turns)

    def clear(self) -> None:
        """Remove all stored turns."""
        self._turns.clear()


# ---------------------------------------------------------------------------
# LangChain agent runtime
# ---------------------------------------------------------------------------


class LangChainAgentRuntime:
    """LangChain-wired runtime adapter for the agent layer.

    Delegates to :class:`~agent.service.AgentService` for tool invocation,
    uses LangChain prompt templates for summary formatting, and validates
    every output against the typed agent schemas before returning.

    Optionally maintains a session-scoped :class:`ConversationContext` for
    recent-turn carryover.  Context is in-memory only — it is not persisted
    and does not survive process restarts.

    Args:
        service: The :class:`~agent.service.AgentService` instance.
        adapter: The :class:`~agent.mcp_adapter.MCPAdapter` instance used to
            create LangChain tool bindings.
        enable_context: When ``True``, maintain a per-instance conversation
            context.  Defaults to ``False``.
        max_context_turns: Maximum number of turns to retain when context is
            enabled.
    """

    def __init__(
        self,
        service: AgentService,
        adapter: MCPAdapter,
        *,
        enable_context: bool = False,
        max_context_turns: int = _DEFAULT_MAX_TURNS,
    ) -> None:
        self._service = service
        self._adapter = adapter
        self._context: ConversationContext | None = (
            ConversationContext(max_turns=max_context_turns) if enable_context else None
        )

        # Lazily import tool factories to avoid circular deps and keep the
        # module importable even when tests don't exercise tool creation.
        from agent.runtime.tools import (
            create_macro_snapshot_tool,
            create_signal_engine_tool,
        )

        self._tools = [
            create_signal_engine_tool(adapter),
            create_macro_snapshot_tool(adapter),
        ]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def tools(self) -> list[Any]:
        """Bound LangChain tools (read-only access for introspection)."""
        return list(self._tools)

    @property
    def context(self) -> ConversationContext | None:
        """The conversation context, or ``None`` if context is disabled."""
        return self._context

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    async def invoke(self, request: AgentRequestInput) -> AgentRuntimeResult:
        """Dispatch an agent request through the LangChain-wired pipeline.

        Pipeline steps:

        1. Delegate to ``AgentService`` for deterministic tool execution.
        2. Re-format the ``summary`` field using the LangChain prompt template.
        3. Validate the complete result against the output schema.
        4. (Optional) Record the turn in the conversation context.

        Args:
            request: A validated agent request.

        Returns:
            :class:`AgentRuntimeResult` with schema-validated response.

        Raises:
            TypeError: If an unsupported request type is passed.
            OutputValidationError: If the output fails schema validation.
        """
        if isinstance(request, SignalReviewRequest):
            result = await self._invoke_review_signals(request)
        elif isinstance(request, MacroSnapshotSummaryRequest):
            result = await self._invoke_summarize_snapshot(request)
        else:
            raise TypeError(
                f"Unsupported request type: {type(request).__name__}. "
                f"Expected SignalReviewRequest or MacroSnapshotSummaryRequest."
            )

        # Validate at the boundary.
        validate_runtime_result(result)

        # Record turn in context if enabled.
        if self._context is not None:
            self._context.add_turn(
                ConversationTurn(
                    request_type=type(request).__name__,
                    request_snapshot=request.model_dump(mode="json"),
                    response_summary=result.response.summary,
                    success=result.success,
                )
            )

        return result

    # ------------------------------------------------------------------
    # Private dispatchers
    # ------------------------------------------------------------------

    async def _invoke_review_signals(
        self,
        request: SignalReviewRequest,
    ) -> AgentRuntimeResult:
        _log.debug(
            "LangChainAgentRuntime: dispatching review_signals (request_id=%s)",
            request.request_id,
        )

        # Step 1 — call the service (MCP boundary preserved).
        response = await self._service.review_signals(request)

        # Step 2 — re-format summary using the prompt template (success only).
        if response.success:
            response = self._reformat_signal_review(response, request)

        return AgentRuntimeResult(
            operation=AgentOperation.REVIEW_SIGNALS,
            response=response,  # type: ignore[arg-type]
        )

    async def _invoke_summarize_snapshot(
        self,
        request: MacroSnapshotSummaryRequest,
    ) -> AgentRuntimeResult:
        _log.debug(
            "LangChainAgentRuntime: dispatching summarize_macro_snapshot (request_id=%s)",
            request.request_id,
        )

        response = await self._service.summarize_macro_snapshot(request)

        if response.success:
            response = self._reformat_snapshot_summary(response)

        return AgentRuntimeResult(
            operation=AgentOperation.SUMMARIZE_MACRO_SNAPSHOT,
            response=response,  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Prompt-driven reformatting
    # ------------------------------------------------------------------

    @staticmethod
    def _reformat_signal_review(
        response: SignalReviewResponse,
        request: SignalReviewRequest,
    ) -> SignalReviewResponse:
        """Re-render the summary using the LangChain prompt template.

        All numeric / metadata fields are preserved from the original response;
        only the ``summary`` string is regenerated.
        """
        from mcp.schemas.run_signal_engine import RunSignalEngineResponse

        # Build a lightweight MCP-response-like object to compute dominance.
        engine_like = RunSignalEngineResponse(
            request_id=response.request_id,
            success=True,
            engine_run_id=response.engine_run_id,
            signals_generated=response.signals_generated,
            buy_signals=response.buy_signals,
            sell_signals=response.sell_signals,
            hold_signals=response.hold_signals,
            execution_time_ms=response.execution_time_ms,
        )
        dominance = dominant_signal_type(engine_like)

        new_summary = render_signal_review_summary(
            signal_ids=", ".join(request.signal_ids),
            country=request.country,
            signals_generated=response.signals_generated,
            buy_signals=response.buy_signals,
            sell_signals=response.sell_signals,
            hold_signals=response.hold_signals,
            dominant_direction=dominance,
            engine_run_id=response.engine_run_id,
            execution_time_ms=f"{response.execution_time_ms:.1f}",
        )

        return SignalReviewResponse(
            request_id=response.request_id,
            timestamp=response.timestamp,
            success=True,
            summary=new_summary,
            engine_run_id=response.engine_run_id,
            signals_generated=response.signals_generated,
            buy_signals=response.buy_signals,
            sell_signals=response.sell_signals,
            hold_signals=response.hold_signals,
            execution_time_ms=response.execution_time_ms,
        )

    @staticmethod
    def _reformat_snapshot_summary(
        response: MacroSnapshotSummaryResponse,
    ) -> MacroSnapshotSummaryResponse:
        """Re-render the summary using the LangChain prompt template."""
        ts_str = (
            response.snapshot_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            if response.snapshot_timestamp is not None
            else "unknown"
        )

        new_summary = render_snapshot_summary(
            country=response.country,
            features_count=response.features_count,
            snapshot_timestamp=ts_str,
        )

        return MacroSnapshotSummaryResponse(
            request_id=response.request_id,
            timestamp=response.timestamp,
            success=True,
            summary=new_summary,
            country=response.country,
            snapshot_timestamp=response.snapshot_timestamp,
            features_count=response.features_count,
        )
