---
name: docker-compose-ops
description: 'Operate repository Docker Compose stacks (dev and webui) with consistent commands for up/down/build/logs/restart and service-scoped actions.'
argument-hint: '[stack: dev|webui] [action: up|down|restart|ps|logs|build|pull|config] [optional service]'
---

# Docker Compose Ops

## Purpose
- Standardize local stack operations for this repository.
- Avoid ad-hoc compose command drift between stacks.
- Provide one consistent entrypoint for routine lifecycle actions.

## Skill Selection (Important)
- Use this skill for normal compose lifecycle operations.
- Use this skill when the user asks to start/stop/rebuild services.
- Do not use this skill for deep runtime troubleshooting.
- For diagnostics, use `docker-runtime-debug`.

## Stacks
- `dev` -> `docker-compose-dev.yml` (references the now-deleted legacy `backend/`; kept for reference only, currently non-functional)
- `webui` -> `docker-compose.yml`

## When to Use
- Bring a stack up/down.
- Rebuild one service or full stack.
- Tail logs for one service or all services.
- Check running service status.

## When Not to Use
- Dependency upgrade requests (use upgrade skills).
- Frontend package operations (use `yarn-frontend-manager`).

## Command
```bash
bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui up
bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui logs webui
bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev restart bot
```

## Execution Notes For Agents
- Run from repository root.
- Prefer `docker compose` plugin syntax and auto-fallback to `docker-compose` when needed.
- For long-running `up` or continuous logs, use async terminal mode.
- For one-shot actions (`ps`, `build`, `pull`, `config`, `down`), use sync mode.
