# Blockers

## 2026-04-17T13:18:51.954Z — Backlog source missing
- **Task**: Select next unfinished task from `/backlog` (lexical order).
- **Blocker**: Required task source directory `/backlog` does not exist in the repository.
- **Impact**: Cannot safely select or execute the next roadmap task under autopilot rules.
- **Attempted checks**:
  - Checked `C:\Users\alstj\macro-invest-agent-system\backlog` directly.
  - Searched for `backlog/**/*.md` in repo root.
- **Recommended next action**:
  - Add backlog task files under `/backlog`, or
  - Provide the canonical backlog path if it differs.
