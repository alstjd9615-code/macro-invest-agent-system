# Decisions

## 2026-04-17 — Encode workflow as agent profile
- **Decision**: Implement the requested procedure as a repository-level Copilot agent profile (`.github/copilot-instructions.md`) plus cloud-agent setup workflow.
- **Reason**: A custom built-in "skill" cannot be created from this repository directly, but agent instructions and setup workflow provide persistent, reusable behavior for future sessions.
- **Tradeoff**: Behavior is instruction-driven rather than a separately invocable skill package.
- **Follow-up**: If a dedicated external skill registry is introduced, migrate this profile into a first-class skill.

## 2026-04-17 — Phase 1 indicator scope
- **Decision**: Start Phase 1 with a strict priority set (CPI, Unemployment, 10Y Yield, PMI, Retail Sales) instead of broad indicator expansion.
- **Reason**: The phase objective emphasizes reliability of ingestion/normalization over breadth.
- **Tradeoff**: Coverage is narrower in this task but quality and freshness tracking are testable end-to-end.
- **Follow-up**: Add remaining Phase 1 indicators in subsequent backlog tasks with the same schema/contracts.

## 2026-04-17 — Checklist-first closure
- **Decision**: Add a dedicated Phase 1 checklist audit document and explicit ingestion-throughput metric before widening indicator coverage.
- **Reason**: The immediate request prioritized checklist verification and observable ingestion foundation quality.
- **Tradeoff**: Added operational/docs artifacts before expanding additional data sources.
- **Follow-up**: Add alert rules for the new ingestion-throughput metric in a later ops-focused Phase 1 task.

## 2026-04-17 — Canonical documentation re-layering
- **Decision**: Adopt strict role separation: concise README + canonical docs + historical logs + scoped backlog.
- **Reason**: Reduce duplication/drift and make ownership of each topic explicit.
- **Tradeoff**: Existing long-form mixed docs were reduced or linked instead of repeated.
- **Follow-up**: Continue consolidating any remaining overlapping legacy docs into canonical files.

## 2026-04-17 — Phase 2 snapshot-first implementation
- **Decision**: Implement Phase 2 in order: snapshot contract → derivation logic → persistence → tests → docs.
- **Reason**: Current stage prioritizes truthful domain contracts over surface/API expansion.
- **Tradeoff**: Snapshot logic is currently service/domain-centric and not yet expanded into broader product surfaces.
- **Follow-up**: Add next Phase 2 backlog tasks for API contract wiring only after domain/persistence coverage is stable.

## 2026-04-17 — Phase 3 contract-first start
- **Decision**: Start Phase 3 with explicit regime schema/vocabulary contracts before any mapping/builder/API expansion.
- **Reason**: Policy prioritizes canonical truth and reviewable contracts over surface completeness.
- **Tradeoff**: Regime outputs are not yet mapped/built; only schema layer is complete in this task.
- **Follow-up**: Implement deterministic snapshot→regime mapping in 0302/0303 tasks.

## 2026-04-17 — Canonical regime vocabulary mapping
- **Decision**: Enforce a deterministic `regime_label -> regime_family` mapping at the domain contract layer (`MacroRegime` validator).
- **Reason**: Prevent inconsistent label/family combinations and keep vocabulary truthful before builder/mapping expansion.
- **Tradeoff**: Callers must provide aligned label/family pairs or receive validation errors.
- **Follow-up**: Reuse this mapping in snapshot-to-regime rule implementation (0303).

## 2026-04-17 — Ordered snapshot-to-regime rule evaluation
- **Decision**: Apply regime mapping rules in explicit order with hard gate rules (`missing/stale -> unclear`, unknown states -> mixed) before thematic labels.
- **Reason**: Avoid overconfident labels when data quality is degraded or state coverage is incomplete.
- **Tradeoff**: Some edge snapshots collapse into `mixed/unclear` rather than more specific labels.
- **Follow-up**: Add confidence layer in 0304 and transition tuning in 0307.

## 2026-04-17 — Coarse-grained confidence over false precision
- **Decision**: Use only `high|medium|low` confidence and deterministic downgrade rules from freshness/degraded/missing/unknown states.
- **Reason**: Current phase prioritizes honest uncertainty handling over speculative precision.
- **Tradeoff**: Confidence is intentionally conservative; nuanced probabilistic scoring is deferred.
- **Follow-up**: Reuse these confidence outputs in regime builder and transition services.

## 2026-04-17 — Contract-first persistence for regimes
- **Decision**: Introduce a dedicated `MacroRegimeRepositoryContract` and keep in-memory adapter as the reference implementation for Phase 3.
- **Reason**: Builder/transition/API layers need stable persistence semantics before durable storage wiring.
- **Tradeoff**: Current runtime persistence is non-durable, but contract compatibility is preserved for later DB adapters.
- **Follow-up**: Add transition-aware save flow and API query layer on top of this repository.

## 2026-04-17 — Transition semantics favor explicit state changes
- **Decision**: Define transition type from label change first, then confidence movement when label is unchanged.
- **Reason**: Label shifts carry stronger macro meaning and should dominate transition classification.
- **Tradeoff**: Intra-label nuances are compressed into strengthening/weakening only.
- **Follow-up**: Keep transition output stable for API consumers and later analytics.

## 2026-04-17 — Regime API read-only shape
- **Decision**: Expose Phase 3 regime outputs via read-only endpoints for latest and comparison views.
- **Reason**: Analysts need inspectable regime/transition state without introducing write-side workflow complexity.
- **Tradeoff**: API currently serves persisted regimes only; build triggering remains service-side.
- **Follow-up**: Add explicit build orchestration endpoint only if backlog requires write actions.

## 2026-04-17 — Regime docs canonical index
- **Decision**: Add a single Phase 3 docs index (`docs/regime_engine.md`) and reference it from README/roadmap.
- **Reason**: Reduce duplication drift across many small regime docs while preserving one-topic-per-file references.
- **Tradeoff**: Readers do one extra click from README to topic docs.
- **Follow-up**: Keep new regime docs linked through the index only.
