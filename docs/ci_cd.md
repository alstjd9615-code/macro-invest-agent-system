# CI/CD Quick Guide

This repository uses separate GitHub Actions workflows for CI and CD.

## Branch flow

- Feature work: push to feature branches + open pull request.
- Mainline deploy: merge/push to `main` only.
- CD never runs from feature branches.

## CI trigger behavior

Workflow: `.github/workflows/ci.yml`

Triggers:
- `pull_request`
- `push` (all branches)

Checks:
1. Backend dependency install (`uv sync --all-extras`)
2. Backend test execution (`uv run pytest tests -q`)
3. Frontend dependency install
   - if `frontend/package.json` exists: `npm ci`
   - otherwise static frontend mode (no npm deps)
4. Frontend production build
   - if `frontend/package.json` exists: `npm run build`
   - otherwise Docker build of frontend image
5. Optional Docker smoke build (API + frontend images)

## CD trigger behavior

Workflow: `.github/workflows/cd.yml`

Triggers:
- `push` to `main`
- manual `workflow_dispatch`

Deploy flow:
1. Validate required secrets
2. SSH to deploy host
3. Sync repository to `origin/main`
4. Rebuild/restart services via Docker Compose
5. Run post-deploy health checks (`/health`, frontend root)

## Required secrets

Set these in repository **Settings → Secrets and variables → Actions**:

- `DEPLOY_HOST`: target server hostname/IP
- `DEPLOY_USER`: SSH username
- `DEPLOY_SSH_KEY`: private SSH key (PEM format)
- `DEPLOY_PATH`: absolute path to checked-out repo on target server
- `DEPLOY_PORT` (optional): SSH port, defaults to `22`

Environment-specific values (host/user/path/port) must be configured per target environment.

## Manual fallback commands

Run on deployment server:

```bash
cd <DEPLOY_PATH>
git fetch --all --prune
git checkout main
git reset --hard origin/main
docker compose up -d --build --remove-orphans
curl -f http://localhost:8000/health
curl -f http://localhost:8080/
```
