# Regime Vocabulary

Canonical source: `domain/macro/regime.py`

This file defines the Phase 3 deterministic regime vocabulary and the canonical
label-to-family mapping used by the regime engine.

## Regime labels

- `goldilocks`
- `disinflation`
- `slowdown`
- `reflation`
- `stagflation_risk`
- `contraction`
- `policy_tightening_drag`
- `mixed`
- `unclear`

## Regime families

- `expansion`
- `inflation_transition`
- `late_cycle`
- `downshift`
- `contraction`
- `uncertain`

## Label-to-family mapping

| regime_label | regime_family |
| --- | --- |
| goldilocks | expansion |
| disinflation | inflation_transition |
| slowdown | downshift |
| reflation | inflation_transition |
| stagflation_risk | late_cycle |
| contraction | contraction |
| policy_tightening_drag | late_cycle |
| mixed | uncertain |
| unclear | uncertain |

`MacroRegime` enforces this mapping: `regime_family` must match
`regime_label`.
