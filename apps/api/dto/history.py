"""History DTOs for the analyst-facing read API.

These DTOs support:

* ``GET /api/regimes/history`` — retrieve recent regime history for an
  as-of date, ordered most recent first.

Design notes
------------
* :class:`HistoricalRegimeDTO` is an API-layer flattening of
  :class:`~domain.macro.history.HistoricalRegimeRecord`.  It carries exactly
  the metadata needed for compare/trend surfaces and read models.
* :class:`RegimeHistoryResponse` wraps the list with aggregate metadata
  (``total``, ``as_of_date``, ``limit_applied``).
* Historical records are **not** the same as degraded or mixed states.
  They are prior observations with their own quality metadata intact.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class HistoricalRegimeDTO(BaseModel, extra="forbid"):
    """A single regime entry in the history list.

    Attributes:
        regime_id: Unique regime identifier.
        as_of_date: Date this regime was built for.
        generated_at: When this regime was created.
        regime_label: Regime label value (e.g. ``"goldilocks"``).
        regime_family: Regime family value (e.g. ``"expansion"``).
        confidence: Confidence level: ``"high"`` / ``"medium"`` / ``"low"``.
        freshness_status: Freshness of the underlying snapshot data.
        degraded_status: Snapshot quality state.
        transition_type: How this regime relates to the prior one.
        transition_from_prior: Prior regime label; ``None`` for the initial.
        changed: ``True`` when label or confidence changed from the prior.
        warnings: Pre-computed analyst-facing warnings.
        is_seeded: ``True`` for bootstrap/synthetic regimes.
        missing_inputs: Indicators missing at build time.
        supporting_snapshot_id: Snapshot that grounded this regime.
    """

    regime_id: str = Field(..., description="Unique regime identifier")
    as_of_date: date = Field(..., description="Date this regime was built for")
    generated_at: datetime = Field(..., description="When this regime was created")
    regime_label: str = Field(..., description="Regime label value")
    regime_family: str = Field(..., description="Regime family value")
    confidence: str = Field(..., description="Confidence level: high / medium / low")
    freshness_status: str = Field(..., description="Freshness of the underlying snapshot data")
    degraded_status: str = Field(..., description="Snapshot quality state")
    transition_type: str = Field(..., description="Transition type vs prior regime")
    transition_from_prior: str | None = Field(
        default=None,
        description="Prior regime label; None for initial regimes",
    )
    changed: bool = Field(
        default=False,
        description="True when regime label or confidence changed from prior",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Pre-computed analyst-facing warnings (degraded, stale, bootstrap, "
            "missing inputs).  Empty when the regime was healthy at creation."
        ),
    )
    is_seeded: bool = Field(
        default=False,
        description="True for bootstrap/synthetic seed regimes",
    )
    missing_inputs: list[str] = Field(
        default_factory=list,
        description="Indicators that were missing when this regime was built",
    )
    supporting_snapshot_id: str = Field(
        default="",
        description="ID of the snapshot that grounded this regime",
    )


class RegimeHistoryResponse(BaseModel, extra="forbid"):
    """Response for ``GET /api/regimes/history``.

    Attributes:
        as_of_date: Reference date the history was retrieved for.
        records: Ordered list of regime entries, most recent first.
        total: Number of records in this response (≤ ``limit_applied``).
        limit_applied: The limit that was applied to this query.
        latest_regime_id: ID of the most recent regime; ``None`` when empty.
        previous_regime_id: ID of the second-most-recent regime; ``None``
            when fewer than two records exist.
    """

    as_of_date: date = Field(..., description="Reference date the history was retrieved for")
    records: list[HistoricalRegimeDTO] = Field(
        default_factory=list,
        description="Historical regime records, most recent first",
    )
    total: int = Field(default=0, ge=0, description="Number of records in this response")
    limit_applied: int = Field(default=10, ge=1, description="Limit applied to this query")
    latest_regime_id: str | None = Field(
        default=None,
        description="ID of the most recent regime; None when the history is empty",
    )
    previous_regime_id: str | None = Field(
        default=None,
        description=(
            "ID of the second-most-recent regime; None when fewer than two records exist. "
            "Used by compare/change surfaces to identify the prior baseline."
        ),
    )
