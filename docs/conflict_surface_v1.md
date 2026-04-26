# Conflict Surface v1

**Canonical source:** `domain/signals/conflict.py`  
**Active workstream:** Multi-Engine Analysis Hub  
**Current phase focus:** Quant + Confidence + Conflict bridge

---

## Purpose

Introduces explicit, lightweight conflict semantics for macro investment signals.

Before this addition, signal conflicts were only implicitly represented via
the `conflicting_drivers` string list.  The Conflict Surface v1 makes the
_degree_ of analytical tension explicit, human-readable, and separately
addressable by product surfaces.

---

## Degraded vs Mixed — critical distinction

| Concept | Meaning | Source field |
|---|---|---|
| **Degraded** | Data/quality/freshness problem — the _input_ is suspect | `is_degraded`, `caveat` |
| **Mixed / Conflicted** | Analytical tension between macro drivers — the _interpretation_ is contested | `conflict_status`, `is_mixed` |

These are orthogonal.  A signal can be:
- healthy + clean (fresh data, coherent drivers)
- healthy + conflicted (fresh data, but drivers point in different directions)
- degraded + clean (stale data, but the available drivers don't conflict)
- degraded + conflicted (worst case)

UI consumers must render these separately and never conflate them.

---

## ConflictStatus vocabulary

| Value | Meaning |
|---|---|
| `clean` | All supporting drivers cohere with the signal direction. No conflict. |
| `tension` | At least one conflicting driver exists, but supporting drivers outnumber them. Conviction is reduced but directional. |
| `mixed` | Conflicting drivers match or outnumber supporting drivers. No clear directional view. |
| `low_conviction` | No supporting drivers at all, or quant overall_support is very weak (<0.35). Treat as indicative only. |

Hierarchy (most to least conviction): **clean > tension > mixed > low_conviction**

---

## ConflictSurface fields (API/DTO)

| Field | Type | Description |
|---|---|---|
| `conflict_status` | `string` | One of: `clean`, `tension`, `mixed`, `low_conviction` |
| `is_mixed` | `bool` | `true` when status is `mixed` or `low_conviction` |
| `conflicting_drivers` | `list[string]` | Macro factors opposing the signal direction |
| `supporting_drivers` | `list[string]` | Macro factors supporting the signal direction |
| `conflict_note` | `string | null` | Analyst-facing explanation; `null` when clean |
| `quant_support_level` | `string` | `strong` (≥0.65) | `moderate` (≥0.40) | `weak` (<0.40) | `unknown` |

---

## Derivation rules

1. **LOW_CONVICTION** when:
   - No supporting drivers, or
   - `quant_overall_support < 0.35` (very weak quant backing).
2. **MIXED** when:
   - `n_conflicting >= n_supporting` (roughly balanced).
3. **TENSION** when:
   - `n_conflicting > 0` but `n_supporting > n_conflicting`.
4. **CLEAN** otherwise.

---

## API contract additions (Chunk 3)

`SignalSummaryDTO` (returned by `GET /api/signals/latest`) now includes:

```json
{
  "conflict_status": "tension",
  "is_mixed": false,
  "conflict_note": "Signal direction supported (3 factors) but 1 conflicting driver reduces conviction. Quant support: strong.",
  "quant_support_level": "strong"
}
```

`SignalOutput` domain model includes a `conflict: ConflictSurface | None` field.

---

## Known limitations / deferred work

- Conflict engine v1 uses raw driver counts only.  A future version should
  use weighted cross-asset conflict resolution.
- No time-series conflict trend tracking.
- The explanation layer does not yet surface conflict notes.
- Full ensemble conflict resolution across asset classes is deferred to a
  future Conflict/Ensemble Engine v2+.
