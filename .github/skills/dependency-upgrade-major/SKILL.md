---
name: dependency-upgrade-major
description: 'Run staged major dependency upgrades with changelog retrieval, checkpointed validation, and iterative compatibility fixes across Python, frontend packages, and container base images.'
argument-hint: '[scope: python|frontend|containers|all] [phase: plan|apply] [--verify]'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md).

# Dependency Upgrade Major

## Purpose
- Execute deliberate major upgrades with explicit migration workflow.
- Fetch changelog links early to speed compatibility fixes.
- Apply upgrades in small batches with validation checkpoints.

## Skill Selection (Important)
- Use this skill for intentional major version upgrades.
- Use this when breaking changes are expected and iterative fixes are acceptable.
- Do not use this skill for routine maintenance updates.
- For patch/minor-style updates, use `dependency-upgrade-safe`.

## Workflow Modes
- `plan`: collect current versions and changelog/release references without changing manifests.
- `apply`: run staged major upgrade commands and checkpoint validations.

## Scopes
- `python`: direct project dependencies in the root pyproject surface.
- `frontend`: package upgrades in the `webui` app.
- `containers`: base image and compose image surface checks.
- `all`: run scopes sequentially with checkpoints.

### Container Base Image Upgrades
When using the `containers` scope, the skill pulls and rebuilds container images. However, **base image version upgrades** (e.g., `python:3.13` → `python:3.14` or `node:24` → `node:25`) must be performed manually in the Dockerfiles:

**Files to update:**
- `Dockerfile`: Python base image (currently `python:3.13-slim-trixie`)
- `webui/Dockerfile`: Node.js base images (currently `node:24-alpine` in all three stages)

**Recommended process:**
1. Check latest base image versions (e.g., `python.org`, `nodejs.org`)
2. Edit Dockerfile base tags to target versions
3. Run `containers plan` to review before applying
4. Run `containers apply` to pull and rebuild with new base images
5. Run `--verify` flag to validate compatibility (tests, lint, health checks)

## Command
```bash
bash .github/skills/dependency-upgrade-major/scripts/upgrade_major.sh all plan
bash .github/skills/dependency-upgrade-major/scripts/upgrade_major.sh all apply --verify
```

## Changelog Retrieval Strategy
- Python packages: read latest metadata and project links from `https://pypi.org/pypi/<package>/json`.
- Node packages: read package metadata via `yarn npm info <package>` or `npm view <package>` fallback.
- Record links and candidate versions before editing manifests.

## Execution Notes For Agents
- Run from repository root.
- Use unsandboxed execution with network enabled when metadata/changelog fetches are blocked.
- Apply upgrades in limited batches and stop on the first failing checkpoint.
- Report blockers and migration steps before continuing to the next batch.
- **For `containers` scope**: Manually update Dockerfile base tags before running the skill. The skill validates and rebuilds, but does not edit Dockerfile tags automatically.
