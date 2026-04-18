"""Signal evaluation service implementation."""

import uuid
from datetime import UTC, datetime

from core.logging.logger import get_logger
from core.metrics import SIGNAL_GENERATION_DURATION
from core.tracing import get_tracer
from core.tracing.span_attributes import SIGNAL_COUNT
from domain.macro.models import MacroSnapshot
from domain.macro.regime import MacroRegime
from domain.signals.engine import SignalEngine
from domain.signals.models import SignalDefinition, SignalOutput, SignalResult
from domain.signals.regime_signal_rules import get_regime_signal_rules
from services.interfaces import SignalServiceInterface

_log = get_logger(__name__)
_tracer = get_tracer(__name__)

class SignalService(SignalServiceInterface):
    """Skeleton implementation of signal service.

    This service coordinates signal evaluation using the SignalEngine.
    Future enhancements will add caching, audit logging, and signal persistence.
    """

    def __init__(self) -> None:
        """Initialize the signal service."""
        self.engine = SignalEngine()

    async def evaluate_signal(
        self, signal_def: SignalDefinition, snapshot: MacroSnapshot
    ) -> dict[str, bool]:
        """Evaluate a signal against macro data.

        Placeholder: returns rule evaluation results.

        Args:
            signal_def: Signal definition with rules
            snapshot: Macro data snapshot

        Returns:
            Dictionary mapping rule names to boolean results

        Raises:
            ValueError: If signal definition is invalid
        """
        if not signal_def.rules:
            raise ValueError("Signal must have at least one rule")

        rule_results: dict[str, bool] = {}
        for rule in signal_def.rules:
            # Placeholder: all rules evaluate to true
            rule_results[rule.name] = True

        return rule_results

    async def run_engine(
        self,
        signal_definitions: list[SignalDefinition],
        snapshot: MacroSnapshot,
    ) -> SignalResult:
        """Run the signal engine against macro data.

        Evaluates all signals and returns comprehensive result.

        Args:
            signal_definitions: List of signals to evaluate
            snapshot: Macro data snapshot

        Returns:
            SignalResult containing all generated signals

        Raises:
            ValueError: If signal definitions are invalid
        """
        if not signal_definitions:
            raise ValueError("At least one signal definition is required")

        _log.debug(
            "service_fetch_started",
            operation="run_engine",
            signal_count=len(signal_definitions),
        )
        with _tracer.start_as_current_span("service.run_signal_engine") as span:
            span.set_attribute("signal.definitions_count", len(signal_definitions))
            with SIGNAL_GENERATION_DURATION.time():
                result = await self.engine.run(signal_definitions, snapshot)
            span.set_attribute(SIGNAL_COUNT, len(result.signals))
        _log.debug(
            "service_fetch_complete",
            operation="run_engine",
            signals_generated=len(result.signals),
        )
        return result

    async def run_regime_grounded_engine(self, regime: MacroRegime) -> SignalResult:
        """Run the regime-grounded signal engine.

        Derives investment signals deterministically from the current macro
        regime label.  Each signal is grounded in the regime with an
        analyst-facing rationale.

        Args:
            regime: The current :class:`~domain.macro.regime.MacroRegime`.

        Returns:
            :class:`~domain.signals.models.SignalResult` with all regime-derived signals.
        """
        run_id = str(uuid.uuid4())
        rules = get_regime_signal_rules(regime.regime_label)
        now = datetime.now(UTC)

        signals: list[SignalOutput] = []
        for rule in rules:
            signal_out = SignalOutput(
                signal_id=rule.signal_id,
                signal_type=rule.signal_type,
                strength=rule.strength,
                score=_strength_to_score(rule.strength),
                triggered_at=now,
                trend=rule.trend,
                rationale=rule.regime_rationale,
                rule_results={"regime_rule": True},
            )
            signals.append(signal_out)

        _log.debug(
            "regime_grounded_engine_complete",
            regime_label=regime.regime_label.value,
            signals_generated=len(signals),
        )
        # SignalResult requires a MacroSnapshot; build a minimal placeholder
        # that carries the regime's as-of date as metadata.
        from domain.macro.enums import DataFrequency, MacroIndicatorType, MacroSourceType
        from domain.macro.models import MacroFeature, MacroSnapshot

        placeholder_feature = MacroFeature(
            indicator_type=MacroIndicatorType.PMI,
            source=MacroSourceType.MARKET_DATA,
            value=0.0,
            timestamp=datetime(regime.as_of_date.year, regime.as_of_date.month, 1, tzinfo=UTC),
            frequency=DataFrequency.MONTHLY,
            country="US",
            metadata={"regime_label": regime.regime_label.value},
        )
        placeholder_snapshot = MacroSnapshot(
            features=[placeholder_feature],
            snapshot_time=now,
            version=1,
        )

        return SignalResult(
            run_id=run_id,
            timestamp=now,
            macro_snapshot=placeholder_snapshot,
            signals=signals,
            success=True,
        )


def _strength_to_score(strength: "SignalStrength") -> float:
    """Map :class:`~domain.signals.enums.SignalStrength` to a numeric score."""
    from domain.signals.enums import SignalStrength

    _map = {
        SignalStrength.VERY_WEAK: 0.1,
        SignalStrength.WEAK: 0.3,
        SignalStrength.MODERATE: 0.5,
        SignalStrength.STRONG: 0.75,
        SignalStrength.VERY_STRONG: 0.95,
    }
    return _map.get(strength, 0.5)
