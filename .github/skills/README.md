# Repository Skills Index

Use this index to choose the correct workflow skill quickly.

## Runtime and Operations

- `docker-compose-ops`
  - File: `./docker-compose-ops/SKILL.md`
  - Use for: start/stop/build/logs/ps/restart/config for `dev` and `next` compose stacks.

- `docker-runtime-debug`
  - File: `./docker-runtime-debug/SKILL.md`
  - Use for: health checks, db readiness, Traefik diagnostics, and log triage.

## Frontend Package Management

- `yarn-frontend-manager`
  - File: `./yarn-frontend-manager/SKILL.md`
  - Use for: install/dev/lint/build/outdated and safe or interactive dependency upgrades across `frontend` and `frontend-next`.

## Dependency Upgrades

- `dependency-upgrade-safe`
  - File: `./dependency-upgrade-safe/SKILL.md`
  - Use for: routine patch/minor-style maintenance and lock refresh flows.

- `dependency-upgrade-major`
  - File: `./dependency-upgrade-major/SKILL.md`
  - Use for: staged major upgrades with changelog lookup and compatibility checkpoints.

## Python Quality and Tests

- `ruff-ty-changed-check`
  - File: `./ruff-ty-changed-check/SKILL.md`
  - Use for: lint and static type checks.

- `pytest-test-runner`
  - File: `./pytest-test-runner/SKILL.md`
  - Use for: runtime test validation and coverage runs.

## Quick Selection Matrix

- Need to run containers normally: `docker-compose-ops`
- Need to debug container behavior: `docker-runtime-debug`
- Need frontend package commands: `yarn-frontend-manager`
- Need low-risk dependency upkeep: `dependency-upgrade-safe`
- Need breaking dependency upgrades: `dependency-upgrade-major`
- Need Python lint/type checks: `ruff-ty-changed-check`
- Need Python tests/coverage: `pytest-test-runner`
