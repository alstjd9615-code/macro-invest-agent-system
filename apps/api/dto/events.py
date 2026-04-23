"""External event DTOs for the analyst-facing read API (Chapter 7)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExternalEventDTO(BaseModel, extra="forbid"):
    """Read model for a single normalized external event.

    Attributes:
        event_id: Unique identifier for the event record.
        event_type: Analyst-meaningful event category.
        title: Short scannable human-readable title.
        summary: Longer analyst-facing description; ``None`` when unavailable.
        entity: Named entity associated with the event; ``None`` when not applicable.
        region: Geographic region scope; ``None`` when not region-specific.
        market_scope: Asset classes or markets affected.
        occurred_at: UTC datetime when the event actually occurred.
        published_at: UTC datetime when the event was published; ``None`` when
            not separately tracked.
        ingested_at: UTC datetime when this record was created.
        source: Human-readable source name.
        source_url: URL to the original source; ``None`` when unavailable.
        provider: Internal provider/connector identifier; ``None`` when ad-hoc.
        freshness: Staleness classification (fresh / recent / stale / unknown).
        provenance: Machine-readable provenance note.
        reliability_tier: Heuristic source reliability classification.
        tags: Normalized taxonomy tags.
        affected_domains: Macro domains this event may affect.
        status: Lifecycle/quality status of the record.
        raw_payload_ref: Opaque reference to the original raw source payload;
            ``None`` when not stored.
        metadata: Supplemental key/value pairs.
    """

    event_id: str
    event_type: str
    title: str
    summary: str | None = None
    entity: str | None = None
    region: str | None = None
    market_scope: list[str] = Field(default_factory=list)
    occurred_at: datetime
    published_at: datetime | None = None
    ingested_at: datetime
    source: str
    source_url: str | None = None
    provider: str | None = None
    freshness: str
    provenance: str
    reliability_tier: str
    tags: list[str] = Field(default_factory=list)
    affected_domains: list[str] = Field(default_factory=list)
    status: str
    raw_payload_ref: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class EventsRecentResponse(BaseModel, extra="forbid"):
    """Response model for ``GET /api/events/recent``."""

    events: list[ExternalEventDTO] = Field(default_factory=list)
    total: int = Field(description="Number of events in this response")
    limit_applied: int = Field(description="The limit that was applied")
