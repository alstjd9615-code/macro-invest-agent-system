"""Macro ingestion service.

Orchestrates the full ingestion cycle:

1. Fetch raw macro features from a :class:`~core.contracts.macro_data_source.MacroDataSourceContract`.
2. Compute deterministic derived fields (``features_count``, ``ingested_at``).
3. Wrap the features in a :class:`~pipelines.ingestion.models.FeatureSnapshot`.
4. Persist the snapshot via a :class:`~core.contracts.feature_store_repository.FeatureStoreRepositoryContract`.
5. Return the persisted snapshot to the caller.

Design principles
-----------------
* **No side effects beyond the repository**: the service fetches from the
  source and writes to the repository only.
* **Deterministic features**: given the same source data, the output snapshot
  is always structurally identical (same field values).
* **Error-safe**: ``RuntimeError`` is raised (not swallowed) when the source
  returns no features, so callers can handle empty-data scenarios explicitly.
* **No direct pipeline dependencies**: this service does not import from the
  ``agent`` or ``mcp`` layers.
"""

from __future__ import annotations

from core.contracts.feature_store_repository import FeatureStoreRepositoryContract
from core.contracts.macro_data_source import MacroDataSourceContract
from core.exceptions.base import ProviderError
from core.logging.logger import get_logger
from core.tracing import get_tracer
from core.tracing.span_attributes import (
    COUNTRY,
    FEATURES_COUNT,
    INDICATOR_COUNT,
    PIPELINE_RUN_ID,
    SOURCE_ID,
)
from domain.macro.enums import MacroIndicatorType
from pipelines.ingestion.models import FeatureSnapshot

_log = get_logger(__name__)
_tracer = get_tracer(__name__)

# Default set of indicators fetched when the caller does not specify any.
DEFAULT_INDICATORS: list[str] = [
    MacroIndicatorType.GDP.value,
    MacroIndicatorType.INFLATION.value,
    MacroIndicatorType.UNEMPLOYMENT.value,
    MacroIndicatorType.INTEREST_RATE.value,
    MacroIndicatorType.BOND_YIELD.value,
]


class MacroIngestionService:
    """Orchestrates macro feature ingestion and persistence.

    Fetches raw macro features from a configured data source, wraps them in a
    :class:`~pipelines.ingestion.models.FeatureSnapshot`, and persists them via
    the feature-store repository.

    Args:
        source: A :class:`~core.contracts.macro_data_source.MacroDataSourceContract`
            implementation (e.g. :class:`~adapters.sources.fixture_macro_data_source.FixtureMacroDataSource`).
        repository: A :class:`~core.contracts.feature_store_repository.FeatureStoreRepositoryContract`
            implementation (e.g. :class:`~adapters.repositories.in_memory_feature_store.InMemoryFeatureStore`).

    Example::

        from adapters.sources.fixture_macro_data_source import FixtureMacroDataSource
        from adapters.repositories.in_memory_feature_store import InMemoryFeatureStore
        from pipelines.ingestion.macro_ingestion_service import MacroIngestionService

        service = MacroIngestionService(
            source=FixtureMacroDataSource(),
            repository=InMemoryFeatureStore(),
        )
        snapshot = await service.ingest(country="US")
    """

    def __init__(
        self,
        source: MacroDataSourceContract,
        repository: FeatureStoreRepositoryContract,
    ) -> None:
        self._source = source
        self._repository = repository

    async def ingest(
        self,
        country: str,
        indicators: list[str] | None = None,
    ) -> FeatureSnapshot:
        """Fetch, snapshot, and persist macro features for a country.

        Args:
            country: ISO 3166-1 alpha-2 country code (e.g. ``"US"``).
            indicators: Indicator names to fetch.  Defaults to
                :data:`DEFAULT_INDICATORS` when ``None``.

        Returns:
            The persisted :class:`~pipelines.ingestion.models.FeatureSnapshot`.

        Raises:
            RuntimeError: If the data source returns no features for the
                requested indicators.
        """
        effective_indicators = indicators if indicators is not None else DEFAULT_INDICATORS
        _log.info(
            "ingestion_started",
            country=country,
            source=self._source.source_id,
            indicator_count=len(effective_indicators),
        )

        with _tracer.start_as_current_span("pipeline.ingest") as span:
            span.set_attribute(COUNTRY, country)
            span.set_attribute(SOURCE_ID, self._source.source_id)
            span.set_attribute(INDICATOR_COUNT, len(effective_indicators))

            try:
                raw_features = await self._source.fetch_raw(
                    country=country, indicators=effective_indicators
                )
            except ProviderError as exc:
                _log.warning(
                    "ingestion_provider_error",
                    country=country,
                    source=self._source.source_id,
                    failure_category=exc.error_code,
                    error=str(exc),
                )
                raise

            if not raw_features:
                raise RuntimeError(
                    f"No macro features returned for country={country!r} "
                    f"from source={self._source.source_id!r}. "
                    f"Requested indicators: {effective_indicators}"
                )

            snapshot = FeatureSnapshot(
                country=country,
                source_id=self._source.source_id,
                features=raw_features,
            )

            await self._repository.save_snapshot(snapshot)

            span.set_attribute(PIPELINE_RUN_ID, snapshot.snapshot_id)
            span.set_attribute(FEATURES_COUNT, snapshot.features_count)

        _log.info(
            "ingestion_complete",
            country=country,
            features_count=snapshot.features_count,
            snapshot_id=snapshot.snapshot_id,
        )

        return snapshot
