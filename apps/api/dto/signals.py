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
* ``is_degraded`` and ``caveat`` are surfaced at both the individual signal
  level and on the response envelope so consumers can render badges at
  either granularity.
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
        rationale: Human-readable regime-grounded rationale for this signal.
        triggered_at: Timestamp when the signal was generated.
        rule_results: Per-rule evaluation results (rule_name → passed).
        rules_passed: Count of rules that passed.
        rules_total: Total number of rules evaluated.
        asset_class: Target asset class (e.g. ``"equities"``, ``"bonds"``).
        supporting_regime: Regime label that grounds this signal.
        supporting_drivers: Macro factors supporting this signal direction.
        conflicting_drivers: Macro factors that reduce signal confidence.
        is_degraded: True when the signal was derived from a degraded/stale/
            low-confidence regime.  Consumers should render a degraded badge.
        caveat: Analyst-facing explanation of why the signal is degraded, or
            ``None`` when ``is_degraded`` is ``False``.
        conflict_status: Conflict/conviction level — ``clean``, ``tension``,
            ``mixed``, or ``low_conviction``.  This is orthogonal to
            ``is_degraded``: degraded = data problem; conflict = analytical
            tension.
        is_mixed: ``True`` when ``conflict_status`` is ``mixed`` or
            ``low_conviction``.
        conflict_note: Analyst-facing explanation of the conflict situation,
            or ``None`` when ``conflict_status`` is ``clean``.
        quant_support_level: Human-readable quant support — ``strong``,
            ``moderate``, ``weak``, or ``unknown``.
    """

    signal_id: str = Field(..., description="Unique signal identifier")
    signal_type: str = Field(..., description="Signal type: buy / sell / hold / neutral")
    strength: str = Field(..., description="Signal confidence: very_weak … very_strong")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    trend: str = Field(default="neutral", description="Trend direction: up / down / neutral")
    rationale: str = Field(default="", description="Regime-grounded analyst rationale")
    triggered_at: datetime = Field(..., description="Timestamp when signal was generated")
    rule_results: dict[str, bool] = Field(
        default_factory=dict, description="Per-rule evaluation results"
    )
    rules_passed: int = Field(default=0, ge=0, description="Count of rules that passed")
    rules_total: int = Field(default=0, ge=0, description="Total rules evaluated")
    asset_class: str = Field(
        default="",
        description="Target asset class (equities, bonds, commodities, cash, all)",
    )
    supporting_regime: str = Field(
        default="",
        description="Regime label that grounds this signal",
    )
    supporting_drivers: list[str] = Field(
        default_factory=list,
        description="Macro factors supporting this signal direction",
    )
    conflicting_drivers: list[str] = Field(
        default_factory=list,
        description="Macro factors that reduce signal confidence",
    )
    is_degraded: bool = Field(
        default=False,
        description=(
            "True when this signal was derived from a degraded, stale, or low-confidence "
            "regime.  Consumers should render a degraded badge and apply extra caution."
        ),
    )
    caveat: str | None = Field(
        default=None,
        description=(
            "Analyst-facing caveat explaining why this signal is degraded. "
            "None when is_degraded=False."
        ),
    )
    conflict_status: str = Field(
        default="clean",
        description=(
            "Conflict/conviction status: 'clean' | 'tension' | 'mixed' | 'low_conviction'. "
            "Distinct from is_degraded — reflects analytical tension, not data quality. "
            "See Conflict Surface v1 semantics in the API contract docs."
        ),
    )
    is_mixed: bool = Field(
        default=False,
        description=(
            "True when conflict_status is 'mixed' or 'low_conviction'. "
            "Convenience boolean to avoid string comparison in UI rendering."
        ),
    )
    conflict_note: str | None = Field(
        default=None,
        description=(
            "Analyst-facing explanation of why this signal is mixed or low-conviction. "
            "None when conflict_status is 'clean'."
        ),
    )
    quant_support_level: str = Field(
        default="unknown",
        description=(
            "Quant support level: 'strong' | 'moderate' | 'weak' | 'unknown'. "
            "Derived from QuantScoreBundle.overall_support."
        ),
    )


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
        regime_label: Regime label that grounded this signal run; ``None`` when
            signals were derived via the fallback snapshot-based path.
        as_of_date: ISO date string of the regime or snapshot this run was
            grounded in; ``None`` when unavailable.
        is_regime_grounded: True when signals were derived from a persisted
            regime.  False when using the fallback snapshot-based engine.
        status: Product-surface state of this response. One of:
            ``'success'`` — healthy regime-grounded signals;
            ``'degraded'`` — regime-grounded but regime is degraded/stale/low-conf;
            ``'fallback'`` — no persisted regime, snapshot-based fallback used;
            ``'empty'`` — no signals generated.
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
    regime_label: str | None = Field(
        default=None,
        description=(
            "Regime label that grounded this signal run. "
            "None when the fallback snapshot-based engine was used."
        ),
    )
    as_of_date: str | None = Field(
        default=None,
        description=(
            "ISO date string (YYYY-MM-DD) of the regime or snapshot this run was "
            "grounded in.  None when unavailable."
        ),
    )
    is_regime_grounded: bool = Field(
        default=False,
        description=(
            "True when signals were derived from a persisted macro regime. "
            "False when using the fallback snapshot-based engine."
        ),
    )
    status: str = Field(
        default="success",
        description=(
            "Product-surface state of this signal response. "
            "One of: 'success', 'degraded', 'fallback', 'empty'. "
            "'success' = healthy regime-grounded signals; "
            "'degraded' = regime-grounded but regime is degraded/stale/low-confidence; "
            "'fallback' = no persisted regime, snapshot-based fallback used; "
            "'empty' = no signals generated."
        ),
    )
