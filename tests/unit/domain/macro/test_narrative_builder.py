"""Tests for the regime narrative builder."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from domain.macro.narrative_builder import build_regime_narrative
from domain.macro.regime import (
    MacroRegime,
    RegimeConfidence,
    RegimeLabel,
    RegimeTransition,
    RegimeTransitionType,
)
from domain.macro.snapshot import DegradedStatus
from pipelines.ingestion.models import FreshnessStatus


def _regime(
    *,
    label: RegimeLabel = RegimeLabel.GOLDILOCKS,
    confidence: RegimeConfidence = RegimeConfidence.HIGH,
    freshness: FreshnessStatus = FreshnessStatus.FRESH,
    degraded: DegradedStatus = DegradedStatus.NONE,
    transition_type: RegimeTransitionType = RegimeTransitionType.INITIAL,
    transition_from_prior: str | None = None,
    supporting_states: dict[str, str] | None = None,
    missing_inputs: list[str] | None = None,
) -> MacroRegime:
    from domain.macro.regime import REGIME_LABEL_FAMILY_MAP

    family = REGIME_LABEL_FAMILY_MAP[label]
    return MacroRegime(
        as_of_date=date(2026, 4, 1),
        regime_timestamp=datetime(2026, 4, 1, tzinfo=UTC),
        regime_label=label,
        regime_family=family,
        supporting_snapshot_id="snap-test",
        confidence=confidence,
        freshness_status=freshness,
        degraded_status=degraded,
        transition=RegimeTransition(
            transition_from_prior=transition_from_prior,
            transition_type=transition_type,
            changed=transition_type == RegimeTransitionType.SHIFT,
        ),
        supporting_states=supporting_states
        or {
            "growth_state": "accelerating",
            "inflation_state": "cooling",
            "labor_state": "tight",
            "policy_state": "neutral",
            "financial_conditions_state": "neutral",
        },
        missing_inputs=missing_inputs or [],
    )


class TestBuildRegimeNarrative:
    def test_returns_expected_keys(self) -> None:
        narrative = build_regime_narrative(_regime())
        assert "summary" in narrative
        assert "rationale_points" in narrative
        assert "regime_label" in narrative
        assert "regime_context" in narrative
        assert "generated_at" in narrative

    def test_summary_is_non_empty_string(self) -> None:
        narrative = build_regime_narrative(_regime())
        assert isinstance(narrative["summary"], str)
        assert len(str(narrative["summary"])) > 50

    def test_rationale_points_is_list(self) -> None:
        narrative = build_regime_narrative(_regime())
        points = narrative["rationale_points"]
        assert isinstance(points, list)
        assert len(points) >= 3

    def test_regime_label_matches(self) -> None:
        narrative = build_regime_narrative(_regime(label=RegimeLabel.CONTRACTION))
        assert narrative["regime_label"] == "contraction"

    def test_regime_context_has_required_keys(self) -> None:
        narrative = build_regime_narrative(_regime())
        ctx = narrative["regime_context"]
        assert isinstance(ctx, dict)
        for key in ("regime_id", "regime_label", "regime_family", "confidence"):
            assert key in ctx

    def test_goldilocks_summary_mentions_risk_on(self) -> None:
        narrative = build_regime_narrative(_regime(label=RegimeLabel.GOLDILOCKS))
        assert "goldilocks" in str(narrative["summary"]).lower() or "risk" in str(
            narrative["summary"]
        ).lower()

    def test_contraction_summary_mentions_contraction(self) -> None:
        narrative = build_regime_narrative(_regime(label=RegimeLabel.CONTRACTION))
        assert "contraction" in str(narrative["summary"]).lower()

    def test_stagflation_summary_mentions_inflation(self) -> None:
        narrative = build_regime_narrative(_regime(label=RegimeLabel.STAGFLATION_RISK))
        assert "inflation" in str(narrative["summary"]).lower()

    def test_low_confidence_reflected_in_summary(self) -> None:
        narrative = build_regime_narrative(_regime(confidence=RegimeConfidence.LOW))
        assert "low" in str(narrative["summary"]).lower()

    def test_stale_freshness_reflected_in_summary(self) -> None:
        narrative = build_regime_narrative(
            _regime(freshness=FreshnessStatus.STALE, label=RegimeLabel.SLOWDOWN)
        )
        assert "stale" in str(narrative["summary"]).lower()

    def test_degraded_partial_reflected_in_summary(self) -> None:
        narrative = build_regime_narrative(
            _regime(degraded=DegradedStatus.PARTIAL, label=RegimeLabel.SLOWDOWN)
        )
        assert "partial" in str(narrative["summary"]).lower() or "missing" in str(
            narrative["summary"]
        ).lower()

    def test_missing_inputs_in_rationale(self) -> None:
        narrative = build_regime_narrative(
            _regime(missing_inputs=["pmi", "retail_sales"])
        )
        points_text = " ".join(str(p) for p in narrative["rationale_points"])
        assert "pmi" in points_text
        assert "retail_sales" in points_text

    def test_transition_from_prior_in_rationale(self) -> None:
        narrative = build_regime_narrative(
            _regime(
                transition_type=RegimeTransitionType.SHIFT,
                transition_from_prior="contraction",
            )
        )
        points_text = " ".join(str(p) for p in narrative["rationale_points"])
        assert "contraction" in points_text

    def test_all_five_states_in_rationale(self) -> None:
        narrative = build_regime_narrative(_regime())
        points_text = " ".join(str(p) for p in narrative["rationale_points"])
        for state_label in ("Growth", "Inflation", "Labour", "Policy", "Financial Conditions"):
            assert state_label in points_text

    def test_all_regime_labels_produce_non_empty_summary(self) -> None:
        """Every RegimeLabel must produce a non-empty summary narrative."""
        for label in RegimeLabel:
            narrative = build_regime_narrative(_regime(label=label))
            assert len(str(narrative["summary"])) > 20, f"Empty summary for {label}"
