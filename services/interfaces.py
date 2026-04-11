"""Service layer interface contracts."""

from abc import ABC, abstractmethod

from domain.macro.models import MacroFeature, MacroSnapshot
from domain.signals.models import SignalDefinition, SignalResult


class MacroServiceInterface(ABC):
    """Interface for macro data retrieval and management.

    Defines the contract for services that provide macroeconomic data
    to the signal evaluation layer.
    """

    @abstractmethod
    async def fetch_features(
        self, indicator_types: list[str], country: str = "US"
    ) -> list[MacroFeature]:
        """Fetch macro features for given indicators.

        Args:
            indicator_types: List of indicator types to fetch
            country: Country code (default: "US")

        Returns:
            List of MacroFeature objects

        Raises:
            ValueError: If indicator_types is empty
            RuntimeError: If data fetch fails
        """

    @abstractmethod
    async def get_snapshot(self, country: str = "US") -> MacroSnapshot:
        """Get a complete macro snapshot at current time.

        Args:
            country: Country code (default: "US")

        Returns:
            MacroSnapshot containing all available features

        Raises:
            RuntimeError: If snapshot cannot be created
        """


class SignalServiceInterface(ABC):
    """Interface for signal evaluation and engine execution.

    Defines the contract for services that manage signal evaluation
    against macro data.
    """

    @abstractmethod
    async def evaluate_signal(
        self, signal_def: SignalDefinition, snapshot: MacroSnapshot
    ) -> dict[str, bool]:
        """Evaluate a signal against macro data.

        Args:
            signal_def: Signal definition with rules
            snapshot: Macro data snapshot

        Returns:
            Dictionary mapping rule names to boolean results

        Raises:
            ValueError: If signal definition is invalid
            RuntimeError: If evaluation fails
        """

    @abstractmethod
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
            RuntimeError: If engine execution fails
        """
