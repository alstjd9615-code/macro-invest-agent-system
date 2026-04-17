# Macro Indicator Catalog

Canonical source: `pipelines/ingestion/indicator_catalog.py`

## Phase 1 priority indicators

| Indicator ID | Label | Category | Frequency | Unit | Source | Series ID | Region | Active |
|---|---|---|---|---|---|---|---|---|
| `inflation` | CPI (All Items) | inflation | monthly | index | fred | CPIAUCSL | US | true |
| `unemployment` | Unemployment Rate | labor | monthly | percent | fred | UNRATE | US | true |
| `yield_10y` | 10Y Treasury Yield | policy_rates | daily | percent | fred | DGS10 | US | true |
| `pmi` | ISM Manufacturing PMI | growth | monthly | index | fred | NAPM | US | true |
| `retail_sales` | Retail Sales | growth | monthly | usd_millions | fred | RSAFS | US | true |

## Notes

- This file is the canonical documentation layer.
- Backlog tasks should reference this file instead of duplicating catalog details.
