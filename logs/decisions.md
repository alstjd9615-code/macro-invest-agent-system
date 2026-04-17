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
