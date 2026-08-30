---
name: yarn-frontend-manager
description: 'Manage Yarn workflows across both frontend projects, including install/dev/lint/build/outdated and safe or interactive upgrades with project-aware command differences.'
argument-hint: '[app: frontend|next|all] [action: install|dev|build|lint|outdated|upgrade-safe|upgrade-interactive|dedupe]'
---

# Yarn Frontend Manager

## Purpose
- Standardize package management for both frontend applications.
- Handle Yarn generation differences automatically.
- Provide safe default dependency update behavior for regular maintenance.

## Skill Selection (Important)
- Use this skill for frontend package installs, script runs, and dependency updates.
- Use this when user asks to run frontend lint/build/dev commands.
- Do not use this skill for Docker lifecycle operations.
- Do not use this skill for Python dependency changes.

## Apps
- `frontend` -> legacy Vue app, Yarn Berry style lock + `packageManager` metadata.
- `next` -> Next.js app, Yarn Classic lockfile format.
- `all` -> run selected action in both app folders sequentially.

## Actions
- `install`: install dependencies with app-specific defaults.
- `dev`: run local dev command.
- `build`: run production build command.
- `lint`: run lint command.
- `outdated`: inspect outdated dependencies.
- `upgrade-safe`: update lockfile within existing semver ranges.
- `upgrade-interactive`: interactive upgrade workflow for broader updates.
- `dedupe`: deduplicate or re-resolve lockfiles using Yarn-native behavior.

## Command
```bash
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh frontend install
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh next lint
bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh all upgrade-safe
```

## Execution Notes For Agents
- Run from repository root.
- Yarn in this environment may require unsandboxed execution because of user-level Yarn config access.
- For `dev`, prefer async mode because process is long-running.
- For one-shot actions, use sync mode.
