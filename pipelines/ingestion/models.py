"""Ingestion pipeline models.

Defines the :class:`FeatureSnapshot` — the unit of data that the ingestion
service produces and the feature-store repository persists.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

from domain.macro.models import MacroFeature


class FeatureSnapshot(BaseModel):
    """A persisted snapshot of macro features produced by an ingestion run.

    A :class:`FeatureSnapshot` represents the output of one ingestion cycle:
    the raw features fetched from a data source, attached to a unique ID,
    a reference country, and an ingestion timestamp.

    Attributes:
        snapshot_id: UUID4 string that uniquely identifies this snapshot.
        country: ISO 3166-1 alpha-2 country code (e.g. ``"US"``).
        source_id: Identifier of the :class:`~core.contracts.macro_data_source.MacroDataSourceContract`
            that provided the raw data.
        ingested_at: UTC timestamp when this snapshot was created.
        features: Non-empty list of :class:`~domain.macro.models.MacroFeature`
            instances included in the snapshot.
        features_count: Derived count of features; always equals
            ``len(features)``.
    """

    snapshot_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUID4 string uniquely identifying this snapshot",
    )
    country: str = Field(..., min_length=1, description="Country code (ISO 3166-1 alpha-2)")
    source_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the data source that provided these features",
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when this snapshot was ingested",
    )
    features: list[MacroFeature] = Field(
        ...,
        min_length=1,
        description="Macro features included in this snapshot (must be non-empty)",
    )
    features_count: int = Field(
        default=0,
        ge=0,
        description="Number of features in this snapshot (derived from len(features))",
    )

    @field_validator("features")
    @classmethod
    def features_must_be_non_empty(cls, v: list[MacroFeature]) -> list[MacroFeature]:
        """Ensure the snapshot contains at least one feature."""
        if not v:
            raise ValueError("FeatureSnapshot must contain at least one feature")
        return v

    def model_post_init(self, __context: object) -> None:
        """Synchronise features_count with the actual features list length."""
        object.__setattr__(self, "features_count", len(self.features))
