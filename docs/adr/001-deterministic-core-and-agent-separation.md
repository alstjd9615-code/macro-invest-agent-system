# ADR-001: Deterministic Core and Agent Separation

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-10 |
| **Deciders** | Platform Engineering |
| **Tags** | architecture, agents, domain, mcp |

---

## Context

This platform uses AI agents (LLM-backed) to help users understand investment signals derived from
macroeconomic data. A critical design question arose early:

> **Should AI agents be allowed to compute, modify, or invent investment signals?**

The answer has significant implications for reproducibility, auditability, testability, and
regulatory appropriateness of the platform.

### Forces at play

1. **Reproducibility**: Investment signals must be deterministic. Given the same macro data,
   the platform must always produce the same signal. LLMs are probabilistic — they cannot
   guarantee identical outputs.

2. **Auditability**: Any decision derived from this platform must be traceable back to an
   explicit, documented function call with explicit inputs and outputs. "The model said so"
   is not an acceptable audit trail.

3. **Testability**: Domain functions can be fully unit-tested with simple input/output assertions.
   LLM behaviour cannot be unit-tested in the same way — only evaluated against golden fixtures.

4. **Separation of concerns**: Agents are excellent at summarising, explaining, and reviewing
   structured data. They are not reliable for numerical computation or rule application.

5. **Security**: Allowing agents to override domain logic creates a prompt-injection vector where
   an adversarial input could cause the agent to produce a fraudulent signal.

---

## Decision

**All investment logic lives in `domain/`, outside the agent layer.**

Specifically:

1. Feature computation (`domain/macro/features.py`) and signal generation
   (`domain/signals/engine.py`) are **pure Python functions** with no LLM involvement.

2. AI agents access domain outputs **exclusively through read-only MCP tools** in `mcp/tools/`.
   Agents never import from `domain/` directly.

3. MCP tools are **query-only** in the MVP. No MCP tool mutates state.

4. Agents are limited to **summarising, reviewing, and explaining** the structured outputs that
   domain functions produce. They cannot change those outputs.

5. Every signal result includes the **input snapshot** and **feature values** used to produce it,
   so that any agent explanation can be verified against a deterministic re-run.

---

## Consequences

### Positive

- Signal computation is fully unit-testable and reproducible.
- Audit trail is always traceable to a pure function call.
- Agent prompt injection cannot compromise domain logic.
- Domain layer has no dependency on any AI framework — it remains lightweight and portable.
- The evaluation harness (`evals/`) can test agent behaviour independently of domain correctness.

### Negative / Trade-offs

- More boilerplate: every new capability requires both a domain function **and** an MCP tool
  schema before agents can use it.
- Agents cannot use their reasoning ability to adjust signals based on context they observe —
  this is intentional but limits flexibility.
- MCP tool schemas must be kept in sync with domain function signatures. A mismatch causes
  a runtime error rather than a compile-time error.

### Mitigations

- MCP input/output schemas are Pydantic v2 models. Pydantic validation catches schema mismatches
  at tool-call time.
- The engineering rules document explicitly forbids direct `domain/` imports from agent code.
- CI enforces that all tests (including MCP contract tests) pass before merge.

---

## Alternatives Considered

### Alternative A: Allow agents to call domain functions directly

**Rejected** because it would make the agent layer responsible for managing domain function
signatures, input preparation, and error handling. This collapses the separation of concerns
and makes prompt-injection attacks on domain logic possible.

### Alternative B: Use the LLM to generate signals, validated post-hoc

**Rejected** because LLM outputs are probabilistic. Even with a post-hoc validator, the platform
cannot guarantee that the same inputs always produce the same output — a fundamental requirement.

### Alternative C: Let agents write back to a "signals draft" table

**Rejected** for the MVP. Write-capable MCP tools would require access control, conflict
resolution, and audit logging that are out of scope for Phase 1. Revisit in Phase 3+ if
there is a clear use case for agent-assisted annotation.

---

## Related

- [docs/engineering_rules.md](../engineering_rules.md) — Rule 3 (Deterministic Core) and Rule 4 (Agent Boundary Rules)
- [docs/project_brief.md](../project_brief.md) — Architecture summary
- `core/exceptions/base.py` — `MCPToolError` and `DomainError` subtypes
- `core/schemas/common.py` — Typed boundary schemas
