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


class RegimeDeltaDTO(BaseModel, extra="forbid"):
    """Structured change between the current and prior regime.

    Produced by the Change Detection Engine v1 and surfaced in
    ``/api/regimes/compare`` and ``/api/regimes/history``.

    Severity is **explicitly heuristic** (v1) — not statistically calibrated.
    See ``docs/regime_transition_rules.md`` for the full heuristic specification.

    Attributes:
        is_initial: True when there is no prior regime.
        label_changed: True when the regime label differs.
        family_changed: True when the regime family differs.
        confidence_changed: True when the confidence level differs.
        confidence_direction: ``"improved"`` / ``"weakened"`` / ``"unchanged"``
            / ``"not_applicable"`` (initial).
        severity: Heuristic severity — ``"unchanged"`` / ``"minor"`` /
            ``"moderate"`` / ``"major"``.
        changed_dimensions: Dimension names that changed
            (``"label"``, ``"family"``, ``"confidence"``).
        prior_label: Prior regime label; ``None`` for initial.
        prior_family: Prior regime family; ``None`` for initial.
        prior_confidence: Prior confidence; ``None`` for initial.
        label_transition: Human-readable label transition string; ``None``
            when label did not change.
        confidence_transition: Human-readable confidence transition; ``None``
            when confidence did not change.
        is_regime_transition: True when a regime label change occurred.
        notable_flags: Analyst-facing flags (e.g. ``"cross_family_transition"``).
        severity_rationale: Short analyst explanation of the severity assignment.
    """

    is_initial: bool = Field(default=False)
    label_changed: bool = Field(default=False)
    family_changed: bool = Field(default=False)
    confidence_changed: bool = Field(default=False)
    confidence_direction: str = Field(
        default="not_applicable",
        description="improved | weakened | unchanged | not_applicable",
    )
    severity: str = Field(
        default="unchanged",
        description=(
            "Heuristic change severity (v1, not statistically calibrated): "
            "unchanged | minor | moderate | major"
        ),
    )
    changed_dimensions: list[str] = Field(
        default_factory=list,
        description="Dimensions that changed: 'label', 'family', 'confidence'",
    )
    prior_label: str | None = Field(default=None)
    prior_family: str | None = Field(default=None)
    prior_confidence: str | None = Field(default=None)
    label_transition: str | None = Field(
        default=None,
        description="Human-readable label transition (e.g. 'goldilocks → slowdown')",
    )
    confidence_transition: str | None = Field(
        default=None,
        description="Human-readable confidence transition (e.g. 'high → medium')",
    )
    is_regime_transition: bool = Field(
        default=False,
        description="True when a regime label change occurred",
    )
    notable_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Notable analyst flags: 'cross_family_transition', "
            "'high_severity_destination', 'confidence_jump'"
        ),
    )
    severity_rationale: str = Field(
        default="",
        description="Short analyst-facing explanation of the severity assignment",
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
    delta: RegimeDeltaDTO | None = Field(
        default=None,
        description=(
            "Structured change object from the Change Detection Engine v1. "
            "Present when a baseline is available (baseline_available=True). "
            "None when this is the initial regime or no prior exists. "
            "Severity is heuristic (v1) — see severity_rationale for explanation."
        ),
    )
