"""Contract for macro regime persistence adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from domain.macro.regime import MacroRegime


class MacroRegimeRepositoryContract(ABC):
    @abstractmethod
    async def save_regime(self, regime: MacroRegime) -> None:
        """Persist a macro regime."""

    @abstractmethod
    async def get_regime_by_id(self, regime_id: str) -> MacroRegime | None:
        """Retrieve a regime by ID."""

    @abstractmethod
    async def get_latest_on_or_before(self, as_of_date: date) -> MacroRegime | None:
        """Retrieve latest regime on or before as_of_date."""
