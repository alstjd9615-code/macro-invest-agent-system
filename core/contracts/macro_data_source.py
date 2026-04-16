"""Contract (abstract base class) for macro data source adapters.

All concrete adapters — whether backed by fixtures, in-memory stores, or real
external providers such as FRED or World Bank — must implement this contract.

Design notes
------------
* The contract is defined as an ABC to enable isinstance checks and to make
  missing-implementation errors explicit at construction time.
* The ``source_id`` property identifies the adapter so it can be logged and
  stored alongside ingested data.
* All methods are **async** to support both synchronous stub adapters (via
  ``asyncio``-compatible returns) and future I/O-bound provider adapters.
* The contract is **read-only** — no method modifies external state.

Error contract
--------------
Concrete adapters MUST raise typed exceptions from
:mod:`core.exceptions.base`, not bare ``RuntimeError``:

* :class:`~core.exceptions.base.ProviderTimeoutError` — request timed out.
* :class:`~core.exceptions.base.ProviderHTTPError` — non-2xx HTTP response.
* :class:`~core.exceptions.base.ProviderNetworkError` — network I/O failure.

This allows callers to distinguish failure categories without parsing message
strings.  Using ``RuntimeError`` directly is deprecated and will be removed in
a future release.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.macro.models import MacroFeature


class MacroDataSourceContract(ABC):
    """Abstract contract for macro data source adapters.

    Concrete subclasses must implement :meth:`fetch_raw`.

    Attributes:
        source_id: Short identifier for this data source (e.g. ``"fixture"``,
            ``"fred"``, ``"world_bank"``).  Used for logging and stored in
            feature snapshots.
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Short, unique identifier for this data source."""

    @abstractmethod
    async def fetch_raw(
        self,
        country: str,
        indicators: list[str],
    ) -> list[MacroFeature]:
        """Fetch raw macro features for the given country and indicators.

        Args:
            country: ISO 3166-1 alpha-2 country code (e.g. ``"US"``).
            indicators: List of :class:`~domain.macro.enums.MacroIndicatorType`
                string values to fetch.  An empty list should return an empty
                result rather than raising.

        Returns:
            List of :class:`~domain.macro.models.MacroFeature` instances.
            The list may be empty if no data is available for the requested
            indicators.

        Raises:
            ProviderTimeoutError: If the upstream provider times out.
            ProviderHTTPError: If the upstream provider returns a non-2xx
                HTTP status.
            ProviderNetworkError: On OS-level / network I/O failure.
        """
