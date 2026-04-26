# Copilot Agent Profile — Backlog Autopilot

Use this profile when running in autopilot mode for this repository.

## Core loop
1. Read `/backlog` and pick the next unfinished task in lexical order.
2. Work exactly one task at a time.
3. Keep scope tight to the selected task.
4. Implement, validate, and document before moving on.
5. Commit exactly one clean commit per completed task.

## Selection rules
- Treat `/backlog` as source of truth.
- Prefer tasks marked `TODO` (or equivalent unfinished state).
- Skip only when blocked by dependencies or missing prerequisites.
- If skipped/blocked, log details in:
  - `/logs/blockers.md`
  - `/logs/progress.md`

## Change rules
- Preserve deterministic core behavior and typed contracts.
- Do not remove trust/provenance/degraded metadata unless task explicitly requires it.
- Avoid unrelated refactors and repository-wide cleanup.
- Reuse existing patterns and interfaces.

## Validation rules
- Run relevant tests/lint/type-check/build/startup checks for the touched scope.
- If failing, attempt up to 3 focused fixes.
- If still blocked, log blocker and leave repo in a coherent state.

## Required updates per completed task
- Mark task file as done (`Status: DONE`, completion date, commit message).
- Update `/logs/progress.md`.
- Update `/logs/changelog.md` when behavior/API/ops/docs changed.
- Update `/logs/decisions.md` for non-obvious tradeoffs.
- Update `README.md` when setup/run/API/service docs changed.

## Commit format
Use one scoped conventional-style commit per completed task, for example:
- `feat(api): add latest snapshot endpoint`
- `fix(frontend): handle empty signal state`
- `docs(readme): document compose services`

Include this trailer:

`Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
