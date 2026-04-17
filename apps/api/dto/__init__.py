"""Product-facing Data Transfer Objects (DTOs) for the analyst API surface.

These DTOs are the stable, frontend-friendly contracts between the FastAPI
read layer and downstream consumers (UI, dashboards, integrations).

Design constraints
------------------
* **Frontend-optimised**: fields are explicit, enum-typed, and named for
  rendering without additional client-side logic.
* **Trust-visible**: every response carries a :class:`~apps.api.dto.trust.TrustMetadata`
  block exposing freshness, degraded, and source attribution state.
* **Read-only**: no write-capable fields or mutation payloads are defined here.
* **Deterministic**: values come from the deterministic domain layer; no
  LLM-generated text overrides numeric or categorical fields.
"""
