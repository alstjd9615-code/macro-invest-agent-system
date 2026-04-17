# Regime Transition Rules

Canonical source: `domain/macro/regime_transition.py`

Transition classification compares current regime to prior stored regime.

## Rules

1. No prior regime -> `initial` (changed: false)
2. Regime label changed -> `shift` (changed: true)
3. Same label, confidence rank improved -> `strengthening` (changed: true)
4. Same label, confidence rank weakened -> `weakening` (changed: true)
5. Same label, same confidence -> `unchanged` (changed: false)

Confidence rank order: `low < medium < high`.
