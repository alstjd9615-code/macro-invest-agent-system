# State Derivation Rules

Canonical implementation: `domain/macro/snapshot.py`

## Categories and vocabularies

- Growth: `accelerating | slowing | mixed | unknown`
- Inflation: `cooling | sticky | reaccelerating | unknown`
- Labor: `tight | softening | weak | unknown`
- Policy: `restrictive | neutral | easing_bias | unknown`
- Financial conditions: `tight | neutral | loose | unknown`

## Deterministic rule baseline (Phase 2)

### Growth

Inputs:
- `pmi`
- `retail_sales`

Rules:
- `accelerating`: PMI >= 52 and retail_sales >= 0
- `slowing`: PMI < 50
- `mixed`: otherwise
- `unknown`: missing required inputs

### Inflation

Input:
- `inflation` (CPI proxy)

Rules:
- `cooling`: <= 2.5
- `sticky`: > 2.5 and <= 3.5
- `reaccelerating`: > 3.5
- `unknown`: missing input

### Labor

Input:
- `unemployment`

Rules:
- `tight`: < 4.0
- `softening`: 4.0 to 5.5
- `weak`: > 5.5
- `unknown`: missing input

### Policy

Input:
- `yield_10y`

Rules:
- `restrictive`: >= 4.5
- `neutral`: >= 3.0 and < 4.5
- `easing_bias`: < 3.0
- `unknown`: missing input

### Financial conditions

Inputs:
- `yield_10y` (required)
- `credit_spread` (optional)

Rules:
- `tight`: 10Y >= 4.5 or credit_spread >= 2.0
- `loose`: 10Y < 3.0 and (credit_spread missing or < 1.0)
- `neutral`: otherwise
- `unknown`: missing required 10Y input
