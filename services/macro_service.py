"""Macroeconomic data service implementation skeleton."""

from datetime import datetime

from domain.macro.enums import DataFrequency, MacroIndicatorType, MacroSourceType
from domain.macro.models import MacroFeature, MacroSnapshot
from services.interfaces import MacroServiceInterface


class MacroService(MacroServiceInterface):
    """Skeleton implementation of macro data service.

    This service is a placeholder that demonstrates the interface contract.
    Future implementation will integrate with external data sources
    (FRED, World Bank, etc.) and internal caching.
    """

    async def fetch_features(
        self, indicator_types: list[str], country: str = "US"
    ) -> list[MacroFeature]:
        """Fetch macro features for given indicators.

        Placeholder: returns synthetic data for demonstration.

        Args:
            indicator_types: List of indicator types to fetch
            country: Country code (default: "US")

        Returns:
            List of MacroFeature objects

        Raises:
            ValueError: If indicator_types is empty
        """
        if not indicator_types:
            raise ValueError("At least one indicator type must be specified")

        # Placeholder: return synthetic features
        features: list[MacroFeature] = []
        for indicator_name in indicator_types:
            try:
                indicator = MacroIndicatorType(indicator_name)
                feature = MacroFeature(
                    indicator_type=indicator,
                    source=MacroSourceType.MARKET_DATA,
                    value=50.0,  # Placeholder value
                    timestamp=datetime.utcnow(),
                    frequency=DataFrequency.MONTHLY,
                    country=country,
                    metadata={"status": "placeholder"},
                )
                features.append(feature)
            except ValueError:
                # Invalid indicator type, skip
                continue

        return features

    async def get_snapshot(self, country: str = "US") -> MacroSnapshot:
        """Get a complete macro snapshot at current time.

        Placeholder: returns snapshot with synthetic data.

        Args:
            country: Country code (default: "US")

        Returns:
            MacroSnapshot containing all available features

        Raises:
            RuntimeError: If snapshot cannot be created
        """
        # Placeholder: fetch common indicators
        common_indicators = [
            MacroIndicatorType.GDP.value,
            MacroIndicatorType.INFLATION.value,
            MacroIndicatorType.UNEMPLOYMENT.value,
        ]

        features = await self.fetch_features(common_indicators, country)

        if not features:
            raise RuntimeError(f"Could not fetch macro data for {country}")

        return MacroSnapshot(
            features=features,
            snapshot_time=datetime.utcnow(),
            version=1,
        )
