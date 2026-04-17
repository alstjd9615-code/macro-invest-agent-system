"""Session read routes for the analyst-facing product API.

Routes
------
``GET /api/sessions/{id}``
    Retrieve a session/conversation-thread context record by its identifier.

Design notes
------------
* Sessions are read-only.  The route does not create, update, or delete sessions.
* In the Phase 6 MVP, sessions are stored in-memory.  A real implementation
  would delegate to the context store repository.
* Returns HTTP 404 when the session ID is not found.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Path

from apps.api.dto.sessions import SessionResponse
from apps.api.dto.trust import DataAvailability, FreshnessStatus, TrustMetadata

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# ---------------------------------------------------------------------------
# In-memory session store (placeholder for Phase 6 MVP)
# ---------------------------------------------------------------------------

_store: dict[str, SessionResponse] = {}


def register_session(session: SessionResponse) -> None:
    """Register a session in the in-memory store.  Called by tests or the agent layer."""
    _store[session.session_id] = session


def clear_session_store() -> None:
    """Clear the in-memory session store.  Used in tests."""
    _store.clear()


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session by ID",
    description=(
        "Retrieve a session or conversation-thread context record by its identifier. "
        "Returns session metadata including request history, country context, and "
        "trust metadata. Returns 404 if not found."
    ),
)
async def get_session(
    session_id: str = Path(..., description="Unique session identifier"),
) -> SessionResponse:
    """Retrieve a session by *session_id*.

    Returns HTTP 200 with :class:`~apps.api.dto.sessions.SessionResponse`
    when found, or HTTP 404 when the session does not exist.
    """
    session = _store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )
    return session


# ---------------------------------------------------------------------------
# Helper — create and register a minimal session record
# ---------------------------------------------------------------------------


def create_session(
    session_id: str,
    country: str = "US",
    request_ids: list[str] | None = None,
) -> SessionResponse:
    """Create and register a new session record.

    Args:
        session_id: Unique identifier for this session.
        country: Country context for the session.
        request_ids: Initial list of request IDs.

    Returns:
        The newly created :class:`SessionResponse`.
    """
    now = datetime.now(UTC)
    ids = request_ids or []
    session = SessionResponse(
        session_id=session_id,
        created_at=now,
        updated_at=now,
        country=country,
        request_ids=ids,
        request_count=len(ids),
        trust=TrustMetadata(
            freshness_status=FreshnessStatus.FRESH,
            availability=DataAvailability.FULL,
            is_degraded=False,
        ),
    )
    register_session(session)
    return session
