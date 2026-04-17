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
    REGIME_LABEL_FAMILY_MAP,
    RegimeConfidence,
    RegimeFamily,
    RegimeLabel,
    RegimeTransition,
    RegimeTransitionType,
    regime_family_for_label,
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
    "REGIME_LABEL_FAMILY_MAP",
    "regime_family_for_label",
    "RegimeTransitionType",
    "RegimeTransition",
    "MacroRegime",
]
