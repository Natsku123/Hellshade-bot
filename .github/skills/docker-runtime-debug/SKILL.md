---
name: docker-runtime-debug
description: 'Run deterministic Docker runtime diagnostics for compose stacks, including health checks, db readiness checks, service logs, and Traefik routing triage.'
argument-hint: '[stack: dev|webui] [check: overview|health|db|traefik|logs] [optional service for logs]'
---

# Docker Runtime Debug

## Purpose
- Troubleshoot container runtime failures with a repeatable sequence.
- Inspect service health quickly before deeper debugging.
- Diagnose Traefik and DB connectivity issues in local stacks.

## Skill Selection (Important)
- Use this skill for runtime failures, unhealthy services, or routing issues.
- Use this after stack startup when behavior is incorrect.
- Do not use this skill for routine start/stop operations.
- For lifecycle operations, use `docker-compose-ops`.

## Stacks
- `dev` -> `docker-compose-dev.yml` (references the now-deleted legacy `backend/`; kept for reference only, currently non-functional)
- `webui` -> `docker-compose.yml`

## Checks
- `overview`: show ps + recent logs snapshot.
- `health`: print health status where available.
- `db`: run postgres readiness checks in the db container.
- `traefik`: show Traefik logs and quick localhost route probes.
- `logs`: follow logs for one service or all services.

## Command
```bash
bash .github/skills/docker-runtime-debug/scripts/runtime_debug.sh webui overview
bash .github/skills/docker-runtime-debug/scripts/runtime_debug.sh webui db
bash .github/skills/docker-runtime-debug/scripts/runtime_debug.sh dev traefik
```

## Execution Notes For Agents
- Run from repository root.
- Start with `overview`, then narrow to `db` or `traefik` as needed.
- If Traefik docker provider is unstable locally, fallback to file-provider routing pattern in `docker-compose.yml` + `traefik/dynamic.yml`.
