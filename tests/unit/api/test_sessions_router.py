"""Tests for the sessions route — GET /api/sessions/{id}."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.sessions import clear_session_store, create_session


@pytest.fixture(autouse=True)
def _clear_store() -> None:
    """Ensure the session store is clean before and after each test."""
    clear_session_store()
    yield
    clear_session_store()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestSessionsRouter:
    """Tests for GET /api/sessions/{id}."""

    def test_not_found_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/sessions/does-not-exist")
        assert resp.status_code == 404

    def test_found_returns_200(self, client: TestClient) -> None:
        create_session("sess-001")
        resp = client.get("/api/sessions/sess-001")
        assert resp.status_code == 200

    def test_response_fields(self, client: TestClient) -> None:
        create_session("sess-abc", country="GB", request_ids=["req-1", "req-2"])
        resp = client.get("/api/sessions/sess-abc")
        data = resp.json()
        assert data["session_id"] == "sess-abc"
        assert data["country"] == "GB"
        assert data["request_count"] == 2
        assert "req-1" in data["request_ids"]

    def test_trust_metadata_present(self, client: TestClient) -> None:
        create_session("sess-trust")
        resp = client.get("/api/sessions/sess-trust")
        trust = resp.json()["trust"]
        assert "freshness_status" in trust
        assert "availability" in trust

    def test_default_country_is_us(self, client: TestClient) -> None:
        create_session("sess-default")
        resp = client.get("/api/sessions/sess-default")
        assert resp.json()["country"] == "US"

    def test_empty_request_ids(self, client: TestClient) -> None:
        create_session("sess-empty", request_ids=[])
        resp = client.get("/api/sessions/sess-empty")
        data = resp.json()
        assert data["request_count"] == 0
        assert data["request_ids"] == []
