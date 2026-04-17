"""Session DTOs for the analyst-facing read API.

These models are the stable, frontend-friendly contracts for:

* ``GET /api/sessions/{id}`` — retrieve a session or conversation-thread
  context record by its identifier.

Design notes
------------
* Sessions are read-only; this DTO surfaces the stored metadata without
  exposing internal context models.
* ``request_ids`` lists the identifiers of agent requests that were part of
  this session, in chronological order.
* Trust metadata is included so that sessions referencing stale data are
  visibly marked in the UI.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from apps.api.dto.trust import TrustMetadata


class SessionResponse(BaseModel, extra="forbid"):
    """Response for GET /api/sessions/{id}.

    Attributes:
        session_id: Unique session identifier.
        created_at: Timestamp when the session was created.
        updated_at: Timestamp of the last request within this session.
        country: Country code associated with the session context.
        request_ids: Ordered list of request IDs in this session.
        request_count: Total number of requests in this session.
        trust: Trust and freshness metadata.
    """

    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Timestamp when this session was created")
    updated_at: datetime = Field(..., description="Timestamp of the last request in this session")
    country: str = Field(default="US", description="Country code associated with session context")
    request_ids: list[str] = Field(
        default_factory=list,
        description="Chronologically ordered list of request IDs in this session",
    )
    request_count: int = Field(default=0, ge=0, description="Total number of requests")
    trust: TrustMetadata = Field(
        default_factory=TrustMetadata, description="Trust and freshness metadata"
    )
