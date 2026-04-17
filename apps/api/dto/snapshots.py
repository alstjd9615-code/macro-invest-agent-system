"""Snapshot DTOs for the analyst-facing read API.

These models are the stable, frontend-friendly contracts for:

* ``GET /api/snapshots/latest`` — latest macro snapshot for a country.
* ``POST /api/snapshots/compare`` — comparison between current and prior snapshot.

Design notes
------------
* :class:`FeatureDTO` is a flattened representation of a ``MacroFeature``
  without internal type hierarchy so the frontend can render rows directly.
* :class:`FeatureDeltaDTO` adds ``direction`` and ``delta`` columns that
  map directly to table/card UI components.
* :class:`SnapshotLatestResponse` wraps the feature list with trust metadata.
* :class:`SnapshotCompareResponse` wraps the delta list with before/after
  summaries for direct card rendering.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.dto.trust import TrustMetadata

# ChangeDirection is localised here so the product surface does not depend
# on internal domain types directly.
ChangeDirection = Literal["increased", "decreased", "unchanged", "no_prior"]


class FeatureDTO(BaseModel, extra="forbid"):
    """A single macro indicator value, flattened for UI consumption.

    Attributes:
        indicator_type: Machine-readable indicator key (e.g. ``"gdp"``).
        indicator_label: Human-readable display label (e.g. ``"GDP Growth"``).
        value: Numerical indicator value.
        source_id: Data source identifier.
        frequency: Observation frequency (``"daily"``, ``"monthly"``, etc.).
        country: ISO 3166-1 alpha-2 country code; ``None`` if global.
        observed_at: Timestamp when this observation was recorded.
    """

    indicator_type: str = Field(..., description="Machine-readable indicator key")
    indicator_label: str = Field(..., description="Human-readable display label")
    value: float = Field(..., description="Numerical indicator value")
    source_id: str = Field(..., description="Data source identifier")
    frequency: str = Field(..., description="Observation frequency")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code")
    observed_at: datetime = Field(..., description="Timestamp of this observation")


class FeatureDeltaDTO(BaseModel, extra="forbid"):
    """Per-indicator change between a current and prior snapshot.

    Maps directly to a comparison table row or badge in the analyst workbench.

    Attributes:
        indicator_type: Machine-readable indicator key.
        indicator_label: Human-readable display label.
        current_value: Value in the current snapshot.
        prior_value: Value in the prior snapshot; ``None`` if no prior data.
        delta: ``current_value - prior_value``; ``None`` if no prior data.
        direction: One of ``"increased"``, ``"decreased"``, ``"unchanged"``,
            ``"no_prior"``.
        is_significant: Whether the delta is considered significant (future
            threshold support); ``False`` by default.
    """

    indicator_type: str = Field(..., description="Machine-readable indicator key")
    indicator_label: str = Field(..., description="Human-readable display label")
    current_value: float = Field(..., description="Value in the current snapshot")
    prior_value: float | None = Field(default=None, description="Value in the prior snapshot")
    delta: float | None = Field(default=None, description="current_value minus prior_value")
    direction: ChangeDirection = Field(..., description="Direction of change")
    is_significant: bool = Field(
        default=False,
        description="Whether the change is considered significant (threshold-based)",
    )


class SnapshotLatestResponse(BaseModel, extra="forbid"):
    """Response for GET /api/snapshots/latest.

    Attributes:
        country: ISO 3166-1 alpha-2 country code.
        features: Flattened list of macro indicator values.
        features_count: Number of indicators in this snapshot.
        trust: Trust and operational metadata for UI badge rendering.
    """

    country: str = Field(..., description="Country code for this snapshot")
    features: list[FeatureDTO] = Field(default_factory=list, description="Macro indicator values")
    features_count: int = Field(default=0, ge=0, description="Number of features in the snapshot")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )


class PriorFeatureInputDTO(BaseModel, extra="forbid"):
    """Minimal prior snapshot feature data for a comparison request.

    Attributes:
        indicator_type: MacroIndicatorType string value (e.g. ``"gdp"``).
        value: The indicator value at the prior snapshot time.
    """

    indicator_type: str = Field(..., description="Indicator type string value")
    value: float = Field(..., description="Indicator value at the prior snapshot time")


class SnapshotCompareRequest(BaseModel, extra="forbid"):
    """Request body for POST /api/snapshots/compare.

    Attributes:
        country: ISO 3166-1 alpha-2 country code (default ``"US"``).
        prior_snapshot_label: Human-readable label for the prior snapshot
            (e.g. ``"Q1-2026"`` or a date string).
        prior_snapshot_timestamp: Optional timestamp for the prior snapshot;
            used to populate trust metadata.
        prior_features: Per-indicator values from the prior snapshot.
    """

    country: str = Field(default="US", description="Country code (ISO 3166-1 alpha-2)")
    prior_snapshot_label: str = Field(
        ...,
        min_length=1,
        description="Human-readable label for the prior snapshot",
    )
    prior_snapshot_timestamp: datetime | None = Field(
        default=None,
        description="Timestamp of the prior snapshot for trust metadata",
    )
    prior_features: list[PriorFeatureInputDTO] = Field(
        default_factory=list,
        description="Per-indicator values from the prior snapshot",
    )


class SnapshotCompareResponse(BaseModel, extra="forbid"):
    """Response for POST /api/snapshots/compare.

    Carries a UI-ready comparison payload with per-indicator deltas and
    an aggregate change summary.

    Attributes:
        country: Country code for this comparison.
        prior_snapshot_label: Human-readable label for the prior snapshot.
        deltas: Per-indicator change records ready for table rendering.
        changed_count: Number of indicators that increased or decreased.
        unchanged_count: Number of indicators that did not change.
        no_prior_count: Number of indicators with no prior data.
        trust: Trust and freshness metadata.
    """

    country: str = Field(..., description="Country code for this comparison")
    prior_snapshot_label: str = Field(..., description="Label for the prior snapshot")
    deltas: list[FeatureDeltaDTO] = Field(
        default_factory=list, description="Per-indicator comparison records"
    )
    changed_count: int = Field(default=0, ge=0, description="Indicators that changed")
    unchanged_count: int = Field(default=0, ge=0, description="Indicators unchanged")
    no_prior_count: int = Field(default=0, ge=0, description="Indicators with no prior data")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
