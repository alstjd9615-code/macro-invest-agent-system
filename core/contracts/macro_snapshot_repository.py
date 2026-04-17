"""Contract for macro snapshot persistence adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from domain.macro.snapshot import MacroSnapshotState


class MacroSnapshotRepositoryContract(ABC):
    @abstractmethod
    async def save_snapshot(self, snapshot: MacroSnapshotState) -> None:
        """Persist a macro snapshot."""

    @abstractmethod
    async def get_snapshot_by_id(self, snapshot_id: str) -> MacroSnapshotState | None:
        """Retrieve a snapshot by ID."""

    @abstractmethod
    async def get_latest_on_or_before(
        self,
        as_of_date: date,
    ) -> MacroSnapshotState | None:
        """Retrieve latest snapshot on or before as_of_date."""
