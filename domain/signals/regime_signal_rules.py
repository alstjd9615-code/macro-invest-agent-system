"""Deterministic regime-to-signal mapping rules.

Maps each :class:`~domain.macro.regime.RegimeLabel` to a set of investment
signals grounded in the current macro regime.  This is the Rule-Based Macro
Engine layer of the multi-engine analysis hub.

Design principles
-----------------
* Every regime label maps to at least one signal.
* Signal type (BUY/SELL/HOLD/NEUTRAL) and strength are set deterministically.
* Each signal carries a human-readable ``regime_rationale`` explaining why
  the regime implies that signal.
* MIXED and UNCLEAR regimes always map to HOLD/NEUTRAL with LOW-equivalent
  strength to reflect genuine uncertainty.
* All asset classes are represented as plain strings so the signal layer
  remains decoupled from any asset-class enum.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.macro.regime import RegimeLabel
from domain.signals.enums import SignalStrength, SignalType, TrendDirection


@dataclass(frozen=True)
class RegimeSignalRule:
    """A single regime-derived signal rule."""

    signal_id: str
    asset_class: str
    signal_type: SignalType
    strength: SignalStrength
    trend: TrendDirection
    regime_rationale: str


# ---------------------------------------------------------------------------
# Regime → signal rule table
# ---------------------------------------------------------------------------
# Each entry maps a RegimeLabel to a list of RegimeSignalRule objects.
# The list is ordered by asset class priority (equities first).

REGIME_SIGNAL_MAP: dict[RegimeLabel, list[RegimeSignalRule]] = {
    RegimeLabel.GOLDILOCKS: [
        RegimeSignalRule(
            signal_id="goldilocks_equities_buy",
            asset_class="equities",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Goldilocks: growth accelerating with inflation cooling and neutral policy. "
                "Risk-on environment strongly favours equity exposure."
            ),
        ),
        RegimeSignalRule(
            signal_id="goldilocks_bonds_hold",
            asset_class="bonds",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.NEUTRAL,
            regime_rationale=(
                "Goldilocks: neutral policy stance reduces duration risk but growth "
                "momentum limits bond upside. Maintain existing allocation."
            ),
        ),
    ],
    RegimeLabel.DISINFLATION: [
        RegimeSignalRule(
            signal_id="disinflation_bonds_buy",
            asset_class="bonds",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Disinflation: inflation cooling with mixed/slowing growth signals "
                "easing pressure on rates. Duration-extending environment for bonds."
            ),
        ),
        RegimeSignalRule(
            signal_id="disinflation_equities_hold",
            asset_class="equities",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.NEUTRAL,
            regime_rationale=(
                "Disinflation: growth is mixed or slowing, limiting equity upside. "
                "Maintain current exposure; rotate toward quality/defensive."
            ),
        ),
    ],
    RegimeLabel.REFLATION: [
        RegimeSignalRule(
            signal_id="reflation_commodities_buy",
            asset_class="commodities",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Reflation: re-accelerating inflation with growth recovery and easing "
                "policy. Commodity and inflation-linked assets are strongly favoured."
            ),
        ),
        RegimeSignalRule(
            signal_id="reflation_equities_buy",
            asset_class="equities",
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Reflation: easing policy supports equity multiples despite rising "
                "inflation. Cyclical and value tilts preferred."
            ),
        ),
        RegimeSignalRule(
            signal_id="reflation_bonds_sell",
            asset_class="bonds",
            signal_type=SignalType.SELL,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Reflation: re-accelerating inflation erodes real bond returns. "
                "Reduce duration; prefer inflation-linked or floating-rate instruments."
            ),
        ),
    ],
    RegimeLabel.SLOWDOWN: [
        RegimeSignalRule(
            signal_id="slowdown_equities_hold",
            asset_class="equities",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Slowdown: growth slowing with softening labour market. Reduce cyclical "
                "risk; rotate toward defensive and quality factors."
            ),
        ),
        RegimeSignalRule(
            signal_id="slowdown_bonds_buy",
            asset_class="bonds",
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Slowdown: decelerating growth raises probability of policy pivot. "
                "Moderate duration extension attractive."
            ),
        ),
    ],
    RegimeLabel.STAGFLATION_RISK: [
        RegimeSignalRule(
            signal_id="stagflation_equities_sell",
            asset_class="equities",
            signal_type=SignalType.SELL,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Stagflation risk: slowing growth with re-accelerating inflation and "
                "weakening labour market. Worst combination for equity risk premia."
            ),
        ),
        RegimeSignalRule(
            signal_id="stagflation_bonds_sell",
            asset_class="bonds",
            signal_type=SignalType.SELL,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Stagflation risk: inflation re-acceleration limits bond upside. "
                "Prefer inflation-linked; reduce nominal duration."
            ),
        ),
        RegimeSignalRule(
            signal_id="stagflation_commodities_buy",
            asset_class="commodities",
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Stagflation risk: real assets and commodities provide partial hedge "
                "against inflation in a growth-challenged environment."
            ),
        ),
    ],
    RegimeLabel.CONTRACTION: [
        RegimeSignalRule(
            signal_id="contraction_equities_sell",
            asset_class="equities",
            signal_type=SignalType.SELL,
            strength=SignalStrength.VERY_STRONG,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Contraction: broad growth contraction with tight financial conditions "
                "and weak labour market. Maximum risk-off; materially reduce equity exposure."
            ),
        ),
        RegimeSignalRule(
            signal_id="contraction_bonds_buy",
            asset_class="bonds",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.UP,
            regime_rationale=(
                "Contraction: flight-to-safety and expected policy easing support "
                "government bonds strongly. Extend duration in high-quality sovereigns."
            ),
        ),
        RegimeSignalRule(
            signal_id="contraction_cash_hold",
            asset_class="cash",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.STRONG,
            trend=TrendDirection.NEUTRAL,
            regime_rationale=(
                "Contraction: high cash allocation reduces drawdown risk while "
                "awaiting clearer inflection signal."
            ),
        ),
    ],
    RegimeLabel.POLICY_TIGHTENING_DRAG: [
        RegimeSignalRule(
            signal_id="policy_drag_equities_hold",
            asset_class="equities",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Policy tightening drag: restrictive policy and tight financial conditions "
                "are compressing multiples. Limit new equity risk; prefer short-duration "
                "growth and dividend defensives."
            ),
        ),
        RegimeSignalRule(
            signal_id="policy_drag_bonds_sell",
            asset_class="bonds",
            signal_type=SignalType.SELL,
            strength=SignalStrength.MODERATE,
            trend=TrendDirection.DOWN,
            regime_rationale=(
                "Policy tightening drag: elevated yields reflect restrictive stance. "
                "Avoid extending duration until policy pivot is confirmed."
            ),
        ),
    ],
    RegimeLabel.MIXED: [
        RegimeSignalRule(
            signal_id="mixed_equities_hold",
            asset_class="equities",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            trend=TrendDirection.NEUTRAL,
            regime_rationale=(
                "Mixed regime: conflicting macro signals prevent a high-conviction "
                "directional call. Maintain balanced allocation; wait for clearer regime."
            ),
        ),
    ],
    RegimeLabel.UNCLEAR: [
        RegimeSignalRule(
            signal_id="unclear_neutral",
            asset_class="all",
            signal_type=SignalType.NEUTRAL,
            strength=SignalStrength.VERY_WEAK,
            trend=TrendDirection.UNKNOWN,
            regime_rationale=(
                "Unclear regime: insufficient or stale macro data prevents reliable "
                "regime classification. No actionable signal; refresh data and re-evaluate."
            ),
        ),
    ],
}


def get_regime_signal_rules(label: RegimeLabel) -> list[RegimeSignalRule]:
    """Return the list of signal rules for *label*.

    Always returns a non-empty list — falls back to UNCLEAR rules if *label*
    is not present in the map (defensive).
    """
    return REGIME_SIGNAL_MAP.get(label, REGIME_SIGNAL_MAP[RegimeLabel.UNCLEAR])
