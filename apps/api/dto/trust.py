"""Trust metadata types for analyst-facing API responses.

All product-surface responses include a :class:`TrustMetadata` block that
exposes the freshness, degradation, and source-attribution state of the
underlying data so that frontend consumers can render badges and warnings
without reconstructing domain logic.

Enum design notes
-----------------
* :class:`FreshnessStatus` uses explicit labels rather than booleans so that
  the UI can render human-readable badges directly.
* :class:`DataAvailability` covers the four availability states the frontend
  needs to handle: full, partial, degraded, and unavailable.
* :class:`ChangeDirection` mirrors ``domain.macro.comparison.ChangeDirection``
  but lives here so that the product surface has no direct import dependency
  on internal domain types.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FreshnessStatus(StrEnum):
    """Staleness classification of a snapshot or signal result.

    Used to render freshness badges in the analyst workbench.
    """

    FRESH = "fresh"
    """Data was updated within the expected window."""

    STALE = "stale"
    """Data is older than the expected update window but still available."""

    UNKNOWN = "unknown"
    """Freshness could not be determined (e.g., timestamp missing)."""


class DataAvailability(StrEnum):
    """Availability classification for a data payload.

    Allows the frontend to render appropriate empty / warning states.
    """

    FULL = "full"
    """All expected indicators or signals are present."""

    PARTIAL = "partial"
    """Some indicators are present; others are missing or unavailable."""

    DEGRADED = "degraded"
    """Data is available but quality or completeness is below threshold."""

    UNAVAILABLE = "unavailable"
    """No data could be retrieved for this request."""


class SourceAttribution(BaseModel, extra="forbid"):
    """Provenance metadata for a single data source.

    Attributes:
        source_id: Machine-readable source identifier (e.g. ``"fred"``).
        source_label: Human-readable display label (e.g. ``"FRED — Federal Reserve"``).
        retrieval_timestamp: When the data was retrieved from this source.
    """

    source_id: str = Field(..., description="Machine-readable source identifier")
    source_label: str = Field(..., description="Human-readable display label for this source")
    retrieval_timestamp: datetime | None = Field(
        default=None,
        description="Timestamp when data was retrieved from this source; None if unknown",
    )


class TrustMetadata(BaseModel, extra="forbid"):
    """Trust and operational metadata attached to every product-surface response.

    Frontend consumers use this block to render freshness badges, source
    attribution, and degraded/stale warnings without performing any
    domain-level calculations.

    Attributes:
        snapshot_timestamp: Reference time of the underlying snapshot.
        previous_snapshot_timestamp: Reference time of the prior snapshot used
            in comparison endpoints; ``None`` for non-comparison responses.
        freshness_status: Whether the data is within its expected update window.
        availability: Whether full, partial, degraded, or no data is present.
        is_degraded: Shorthand flag for degraded state (mirrors availability).
        sources: List of data sources that contributed to this response.
        changed_indicators_count: Number of indicators that changed relative
            to the prior snapshot; ``None`` for non-comparison endpoints.
    """

    snapshot_timestamp: datetime | None = Field(
        default=None,
        description="Reference time of the current underlying snapshot",
    )
    previous_snapshot_timestamp: datetime | None = Field(
        default=None,
        description="Reference time of the prior snapshot; None for non-comparison responses",
    )
    freshness_status: FreshnessStatus = Field(
        default=FreshnessStatus.UNKNOWN,
        description="Whether the snapshot data is within its expected update window",
    )
    availability: DataAvailability = Field(
        default=DataAvailability.FULL,
        description="Full / partial / degraded / unavailable data availability classification",
    )
    is_degraded: bool = Field(
        default=False,
        description="True when availability is DEGRADED; shorthand for UI badge rendering",
    )
    sources: list[SourceAttribution] = Field(
        default_factory=list,
        description="Data sources that contributed to this response",
    )
    changed_indicators_count: int | None = Field(
        default=None,
        description=(
            "Number of indicators that changed vs the prior snapshot; "
            "None for non-comparison endpoints"
        ),
    )
    degraded_reason: str | None = Field(
        default=None,
        description=(
            "Machine-readable reason code explaining why this response is degraded. "
            "Examples: 'regime_unavailable_fallback_engine_used', "
            "'stale_data_partial_indicators'. None when not degraded."
        ),
    )
