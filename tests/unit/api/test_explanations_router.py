"""Tests for the explanations route — GET /api/explanations/{id}."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routers.explanations import (
    build_and_register_explanation,
    clear_explanation_store,
)


@pytest.fixture(autouse=True)
def _clear_store() -> Generator[None, None, None]:
    """Ensure the explanation store is clean before and after each test."""
    clear_explanation_store()
    yield
    clear_explanation_store()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestExplanationsRouter:
    """Tests for GET /api/explanations/{id}."""

    def test_not_found_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/explanations/does-not-exist")
        assert resp.status_code == 404

    def test_found_returns_200(self, client: TestClient) -> None:
        build_and_register_explanation(
            run_id="run-abc",
            signal_id="bull_market",
            summary="Bull market conditions confirmed.",
            rationale_points=["GDP > 2%", "Inflation < 4%"],
        )
        resp = client.get("/api/explanations/run-abc:bull_market")
        assert resp.status_code == 200

    def test_response_fields(self, client: TestClient) -> None:
        build_and_register_explanation(
            run_id="run-xyz",
            signal_id=None,
            summary="Snapshot is healthy.",
            rationale_points=["All indicators within range"],
        )
        resp = client.get("/api/explanations/run-xyz")
        data = resp.json()
        assert data["explanation_id"] == "run-xyz"
        assert data["run_id"] == "run-xyz"
        assert data["signal_id"] is None
        assert data["summary"] == "Snapshot is healthy."
        assert len(data["rationale_points"]) == 1

    def test_composite_id_with_signal(self, client: TestClient) -> None:
        build_and_register_explanation(
            run_id="run-001",
            signal_id="recession_warning",
            summary="Recession warning.",
            rationale_points=["Unemployment > 7%", "GDP < 0"],
        )
        resp = client.get("/api/explanations/run-001:recession_warning")
        data = resp.json()
        assert data["signal_id"] == "recession_warning"
        assert data["explanation_id"] == "run-001:recession_warning"

    def test_trust_metadata_present(self, client: TestClient) -> None:
        build_and_register_explanation(
            run_id="run-trust",
            signal_id="bull_market",
            summary="ok",
            rationale_points=[],
        )
        resp = client.get("/api/explanations/run-trust:bull_market")
        trust = resp.json()["trust"]
        assert "freshness_status" in trust
        assert "availability" in trust
        assert trust["freshness_status"] == "fresh"

    def test_different_ids_do_not_collide(self, client: TestClient) -> None:
        build_and_register_explanation("run-A", "s1", "summary A", [])
        build_and_register_explanation("run-B", "s1", "summary B", [])

        resp_a = client.get("/api/explanations/run-A:s1")
        resp_b = client.get("/api/explanations/run-B:s1")
        assert resp_a.json()["summary"] == "summary A"
        assert resp_b.json()["summary"] == "summary B"
