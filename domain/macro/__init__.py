"""Macroeconomic domain models and contracts."""

from domain.macro.comparison import (
    FeatureDelta,
    PriorFeatureInput,
    SnapshotComparison,
    compare_snapshots,
)
from domain.macro.enums import DataFrequency, MacroIndicatorType, MacroSourceType
from domain.macro.models import MacroFeature, MacroSnapshot
from domain.macro.regime import (
    MacroRegime,
    RegimeConfidence,
    RegimeFamily,
    RegimeLabel,
    RegimeTransition,
    RegimeTransitionType,
)

__all__ = [
    "MacroIndicatorType",
    "MacroSourceType",
    "DataFrequency",
    "MacroFeature",
    "MacroSnapshot",
    "PriorFeatureInput",
    "FeatureDelta",
    "SnapshotComparison",
    "compare_snapshots",
    "RegimeLabel",
    "RegimeFamily",
    "RegimeConfidence",
    "RegimeTransitionType",
    "RegimeTransition",
    "MacroRegime",
]
