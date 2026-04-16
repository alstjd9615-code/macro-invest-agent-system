# Release Gating

This document describes which eval sub-suites are required to pass before a
PR can be merged, how to run the full eval suite, how to update prompt drift
fixtures, and what `is_degraded=True` means for downstream consumers.

---

## Required Eval Sub-Suites

All eval sub-suites must pass before merging any PR that touches the agent,
MCP, service, or adapter layers.

| Sub-suite                         | Location                                | Gated? |
|---|---|---|
| Unit tests (core, domain, mcp, services) | `tests/`                           | ✅ Required |
| Multi-turn context                | `evals/multi_turn/`                     | ✅ Required |
| Snapshot comparison               | `evals/comparison/`                     | ✅ Required |
| Provider failure (typed)          | `evals/provider_failure/`               | ✅ Required |
| Schema conformance                | `evals/schema_conformance/`             | ✅ Required |
| Prompt regression / drift         | `evals/prompt_regression/`              | ✅ Required |
| Tracing / observability           | `evals/tracing/`                        | ✅ Required |

---

## Running the Full Eval Suite

```bash
# Run all tests and evals together
python -m pytest tests/ evals/ -v

# Run only evals
python -m pytest evals/ -v

# Run a specific sub-suite
python -m pytest evals/provider_failure/ -v
python -m pytest evals/tracing/ -v
python -m pytest evals/prompt_regression/ -v
```

---

## How to Update Prompt Drift Fixtures

The prompt drift test (`evals/prompt_regression/test_prompt_drift.py`) computes
a SHA-256 hash of each rendered prompt template against a fixed canonical input
set and compares it to stored hashes in:

```
evals/prompt_regression/fixtures/prompt_hashes.json
```

**When to update fixtures:**

Update the fixture hashes ONLY when a prompt template is intentionally changed
(e.g., adding a new field, improving phrasing). Accidental drift — caused by
refactoring unrelated code — should NEVER be silenced by updating fixtures.

**Steps to update:**

1. Make your intentional template change in `agent/prompts/templates.py`.

2. Re-run the failing drift test to see the new hash:

   ```bash
   python -m pytest evals/prompt_regression/test_prompt_drift.py -v
   ```

3. Update `evals/prompt_regression/fixtures/prompt_hashes.json` with the new
   hash values shown in the failure message.

4. Re-run the test to confirm it passes.

5. Commit **both** the template change and the updated fixture in the same PR
   with a clear description of why the template changed.

---

## What `is_degraded=True` Means for Downstream Consumers

The `is_degraded` flag on MCP and agent responses indicates that the response
is **schema-valid** but the underlying data is **incomplete or stale**:

| State                          | `success` | `is_degraded` | `failure_category`      |
|---|---|---|---|
| Clean success                  | `True`    | `False`       | `None`                  |
| Partial data (usable)          | `False`   | `True`        | `PARTIAL_DATA`          |
| Stale data                     | `False`   | `True`        | `STALE_DATA`            |
| Provider hard failure          | `False`   | `False`       | `PROVIDER_*` / `UNKNOWN`|

**Consumer guidance:**

- Always check `success` first. If `False`, inspect `failure_category`.
- If `is_degraded=True`, display a warning to users that the data may be
  incomplete or outdated, but the response can still be used.
- If `is_degraded=False` and `success=True`, the response is clean — proceed
  normally.
- Never silently ignore `is_degraded=True` in production display logic.

---

## PR Checklist Before Merge

Before merging any PR that touches agent, MCP, service, or adapter code:

- [ ] All unit tests pass (`python -m pytest tests/ -v`)
- [ ] All evals pass (`python -m pytest evals/ -v`)
- [ ] No regressions in prompt drift hashes (or fixtures are intentionally
      updated with review)
- [ ] `failure_category` is set on all failure responses (verify with
      `evals/schema_conformance/test_failure_category_schema.py`)
- [ ] New adapters implement `metadata` property and register in `SourceRegistry`
- [ ] New adapters raise typed `ProviderError` subclasses (not `RuntimeError`)
- [ ] New adapters have a corresponding `evals/provider_failure/` eval
- [ ] No secrets, API keys, or PII in any log events (check `fred_fetch_*` events)
- [ ] PR description explains any `is_degraded` or `failure_category` changes

---

## Running a Specific Feature Regression

```bash
# Provider failure scenarios
python -m pytest evals/provider_failure/ -v -k "timeout or http or stale or partial"

# Schema field compliance
python -m pytest evals/schema_conformance/ -v

# Multi-turn degraded flows
python -m pytest evals/multi_turn/test_degraded_turn.py -v

# Tracing / trace_id binding
python -m pytest evals/tracing/ -v
```
