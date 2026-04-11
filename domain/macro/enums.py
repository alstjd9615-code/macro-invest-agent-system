"""Enumerations for macro economic data types and sources."""

from enum import StrEnum


class MacroIndicatorType(StrEnum):
    """Types of macroeconomic indicators."""

    GDP = "gdp"
    INFLATION = "inflation"
    UNEMPLOYMENT = "unemployment"
    INTEREST_RATE = "interest_rate"
    EXCHANGE_RATE = "exchange_rate"
    STOCK_INDEX = "stock_index"
    BOND_YIELD = "bond_yield"
    CREDIT_SPREAD = "credit_spread"
    COMMODITY_PRICE = "commodity_price"
    PMI = "pmi"  # Purchasing Managers' Index


class MacroSourceType(StrEnum):
    """Data sources for macroeconomic indicators."""

    FRED = "fred"  # Federal Reserve Economic Data
    WORLD_BANK = "world_bank"
    IMF = "imf"  # International Monetary Fund
    OECD = "oecd"
    ECB = "ecb"  # European Central Bank
    MARKET_DATA = "market_data"
    CUSTOM = "custom"


class DataFrequency(StrEnum):
    """Frequency of data observations."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
