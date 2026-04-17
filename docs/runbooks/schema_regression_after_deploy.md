# Runbook: Schema Regression After Deploy

**Alert:** `SchemaValidationFailures`

---

## Symptoms

- `macro_platform_schema_validation_failures_total` is non-zero after a deploy.
- Agent responses are failing at the output validation boundary with
  `OutputValidationError`.
- Application logs show events like:
  ```
  Agent response failed schema validation (type=SignalReviewResponse): ...
  ```

---

## Immediate triage

1. **Identify the affected response type:**
   ```promql
   increase(macro_platform_schema_validation_failures_total[10m])
   ```
   The `response_type` label tells you which Pydantic model is failing.

2. **Check application logs for the full validation error:**
   ```bash
   docker compose logs api | jq 'select(.event | contains("schema_validation"))'
   ```
   The `detail` field contains the Pydantic error message, which identifies
   the specific field and constraint that failed.

3. **Check the git log for recent changes to agent schemas or formatters:**
   ```bash
   git log --oneline -20 -- agent/schemas.py agent/formatting/ agent/runtime/
   ```
   Schema regressions typically stem from:
   - A field added to a schema without a default value.
   - A field type narrowed (e.g. `str` → `Literal[...]`).
   - A formatter producing a value outside the schema's allowed range.

---

## Mitigation

### If the regression is in a schema field

The safest fix depends on the type of change:

| Change type | Safe fix |
|---|---|
| Field narrowed without backward compatibility | Widen the type or add a fallback in the formatter |
| New required field without default | Add a default or make the field optional |
| Enum value removed | Re-add the value or update the formatter |

Apply the fix, run tests, and redeploy:
```bash
uv run pytest tests/
# If tests pass:
git commit -m "fix: restore schema compatibility after regression"
# Deploy the fix
```

### Immediate rollback (if fix is not yet ready)

```bash
# Roll back to the previous Docker image
docker compose pull api  # fetch old tag if available
docker compose up -d api

# Or, if using git tags, check out the previous release
git checkout <previous-tag>
docker compose build api
docker compose up -d api
```

### Confirm rollback / fix resolved the issue

```promql
# Should return 0 after fix
increase(macro_platform_schema_validation_failures_total[10m])
```

Run the agent eval suite to confirm no regressions:
```bash
uv run pytest evals/ -m eval
```

---

## Prevention

- Always run `pytest tests/` before merging schema changes.
- The eval harness (`evals/`) exercises round-trips through the full
  agent stack; run it as a gate on changes that touch `agent/schemas.py`
  or `agent/formatting/`.
- Add a Pydantic `model_config = ConfigDict(strict=True)` to catch unexpected
  coercions early.

---

## Escalation path

If the schema failure is in a field that is critical to analyst workflows
(e.g. `signal_direction`, `summary`), set agent responses to return an
explicit error until the fix is deployed, rather than producing silently
degraded output.
