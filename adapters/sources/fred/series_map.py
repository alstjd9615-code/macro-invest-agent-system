"""Mapping from :class:`~domain.macro.enums.MacroIndicatorType` values to FRED series IDs.

This module provides a minimal, intentionally small series map covering the
five indicators in :data:`~pipelines.ingestion.macro_ingestion_service.DEFAULT_INDICATORS`.

References
----------
* GDP (Real): https://fred.stlouisfed.org/series/GDPC1
* CPI (inflation proxy): https://fred.stlouisfed.org/series/CPIAUCSL
* Unemployment rate: https://fred.stlouisfed.org/series/UNRATE
* Federal Funds Rate: https://fred.stlouisfed.org/series/FEDFUNDS
* 10-Year Treasury yield: https://fred.stlouisfed.org/series/DGS10
"""

from __future__ import annotations

from domain.macro.enums import MacroIndicatorType

# Maps each supported MacroIndicatorType to the corresponding FRED series ID.
FRED_SERIES_MAP: dict[MacroIndicatorType, str] = {
    MacroIndicatorType.GDP: "GDPC1",
    MacroIndicatorType.INFLATION: "CPIAUCSL",
    MacroIndicatorType.UNEMPLOYMENT: "UNRATE",
    MacroIndicatorType.INTEREST_RATE: "FEDFUNDS",
    MacroIndicatorType.BOND_YIELD: "DGS10",
}
