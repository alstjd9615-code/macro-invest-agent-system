"""Regime DTOs for analyst-facing read API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class RegimeTransitionDTO(BaseModel, extra="forbid"):
    transition_from_prior: str | None = Field(default=None)
    transition_type: str = Field(default="unknown")
    changed: bool = Field(default=False)


class RegimeLatestResponse(BaseModel, extra="forbid"):
    as_of_date: date
    regime_id: str
    regime_timestamp: datetime
    regime_label: str
    regime_family: str
    confidence: str
    freshness_status: str
    degraded_status: str
    missing_inputs: list[str] = Field(default_factory=list)
    supporting_snapshot_id: str
    supporting_states: dict[str, str] = Field(default_factory=dict)
    transition: RegimeTransitionDTO = Field(default_factory=RegimeTransitionDTO)
    rationale_summary: str = Field(default="")
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Pre-computed analyst-facing warnings summarising degraded, stale, "
            "missing-input, or bootstrap conditions.  Empty list when the regime "
            "is fully healthy.  Intended for direct UI badge / tooltip rendering."
        ),
    )
    status: str = Field(
        default="success",
        description=(
            "Product-surface state of this response. "
            "One of: 'success', 'degraded', 'stale', 'bootstrap'. "
            "'success' = healthy, non-synthetic data. "
            "'degraded' = partial/missing indicators or low confidence. "
            "'stale' = data older than expected freshness window. "
            "'bootstrap' = regime derived from synthetic startup seed data."
        ),
    )
    is_seeded: bool = Field(
        default=False,
        description=(
            "True when this regime was created by the startup bootstrap seeder "
            "from synthetic data rather than from a real ingestion pipeline."
        ),
    )
    data_source: str = Field(
        default="",
        description=(
            "Origin of the data used to derive this regime. "
            "'synthetic_seed' for bootstrap data; empty for production data."
        ),
    )


class RegimeCompareResponse(BaseModel, extra="forbid"):
    as_of_date: date
    baseline_available: bool
    current_regime_label: str
    prior_regime_label: str | None = None
    transition_type: str
    changed: bool
    current_confidence: str
    prior_confidence: str | None = None
    current_rationale_summary: str = Field(
        default="",
        description="Rationale summary for the current regime, surfaced for analyst context.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Analyst-facing warnings from the current regime (degraded, stale, "
            "missing inputs, bootstrap).  Mirrors the field in RegimeLatestResponse."
        ),
    )
    is_seeded: bool = Field(
        default=False,
        description=(
            "True when the current regime was created by the startup bootstrap "
            "seeder from synthetic data."
        ),
    )
