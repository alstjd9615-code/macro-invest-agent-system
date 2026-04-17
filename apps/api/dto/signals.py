"""Signal DTOs for the analyst-facing read API.

These models are the stable, frontend-friendly contracts for:

* ``GET /api/signals/latest`` — latest signal outputs for a country.

Design notes
------------
* :class:`SignalSummaryDTO` flattens a ``SignalOutput`` domain model into
  a row-oriented structure for direct card or table rendering.
* :class:`SignalsLatestResponse` bundles signals with aggregate counts and
  trust metadata.
* The ``strongest_signal`` convenience field reduces client-side max lookup.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from apps.api.dto.trust import TrustMetadata


class SignalSummaryDTO(BaseModel, extra="forbid"):
    """A single evaluated signal, flattened for UI rendering.

    Attributes:
        signal_id: Unique signal identifier.
        signal_type: Type label (``"buy"``, ``"sell"``, ``"hold"``, ``"neutral"``).
        strength: Confidence label (``"weak"``, ``"moderate"``, ``"strong"``, etc.).
        score: Confidence score in the range ``[0.0, 1.0]``.
        trend: Underlying trend direction (``"up"``, ``"down"``, ``"neutral"``).
        rationale: Human-readable explanation of the signal.
        triggered_at: Timestamp when the signal was generated.
        rule_results: Per-rule evaluation results (rule_name → passed).
        rules_passed: Count of rules that passed.
        rules_total: Total number of rules evaluated.
    """

    signal_id: str = Field(..., description="Unique signal identifier")
    signal_type: str = Field(..., description="Signal type: buy / sell / hold / neutral")
    strength: str = Field(..., description="Signal confidence: very_weak … very_strong")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    trend: str = Field(default="neutral", description="Trend direction: up / down / neutral")
    rationale: str = Field(default="", description="Human-readable signal rationale")
    triggered_at: datetime = Field(..., description="Timestamp when signal was generated")
    rule_results: dict[str, bool] = Field(
        default_factory=dict, description="Per-rule evaluation results"
    )
    rules_passed: int = Field(default=0, ge=0, description="Count of rules that passed")
    rules_total: int = Field(default=0, ge=0, description="Total rules evaluated")


class SignalsLatestResponse(BaseModel, extra="forbid"):
    """Response for GET /api/signals/latest.

    Attributes:
        country: Country code for this signal run.
        run_id: Unique signal engine run identifier.
        signals: List of evaluated signal summaries.
        signals_count: Total number of signals.
        buy_count: Number of BUY signals.
        sell_count: Number of SELL signals.
        hold_count: Number of HOLD signals.
        strongest_signal_id: ID of the highest-scoring signal; ``None`` if no
            signals.
        trust: Trust and freshness metadata for UI badge rendering.
    """

    country: str = Field(..., description="Country code for this signal run")
    run_id: str = Field(default="", description="Signal engine run identifier")
    signals: list[SignalSummaryDTO] = Field(
        default_factory=list, description="Evaluated signal summaries"
    )
    signals_count: int = Field(default=0, ge=0, description="Total number of signals")
    buy_count: int = Field(default=0, ge=0, description="Number of BUY signals")
    sell_count: int = Field(default=0, ge=0, description="Number of SELL signals")
    hold_count: int = Field(default=0, ge=0, description="Number of HOLD signals")
    strongest_signal_id: str | None = Field(
        default=None,
        description="ID of the highest-scoring signal; None if no signals",
    )
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
