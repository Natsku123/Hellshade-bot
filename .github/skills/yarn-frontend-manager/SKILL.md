---
name: yarn-frontend-manager
description: 'Manage Yarn workflows for the webui Next.js app, including install/dev/lint/build/outdated and safe or interactive upgrades.'
argument-hint: '[action: install|dev|build|lint|outdated|upgrade-safe|upgrade-interactive|dedupe]'
---

# Yarn Frontend Manager

## Purpose
- Standardize package management for the webui Next.js application.
- Provide safe default dependency update behavior for regular maintenance.

## Skill Selection (Important)
- Use this skill for webui package installs, script runs, and dependency updates.
- Use this when user asks to run webui lint/build/dev commands.
- Do not use this skill for Docker lifecycle operations.
- Do not use this skill for Python dependency changes.

## App
- `webui` -> Next.js app (formerly `frontend-next`), Yarn Classic lockfile format.

## Actions
- `install`: install dependencies (`--ignore-engines`).
- `dev`: run local dev command.
- `build`: run production build command.
- `lint`: run lint command.
- `outdated`: inspect outdated dependencies.
- `upgrade-safe`: update lockfile within existing semver ranges.
- `upgrade-interactive`: interactive upgrade workflow for broader updates.
- `dedupe`: deduplicate or re-resolve lockfiles using Yarn-native behavior.

## Command
```bash
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh install
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh lint
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh upgrade-safe
```

## Execution Notes For Agents
- Run from repository root.
- Yarn in this environment may require unsandboxed execution because of user-level Yarn config access.
- For `dev`, prefer async mode because process is long-running.
- For one-shot actions, use sync mode.
