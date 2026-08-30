---
name: dependency-upgrade-safe
description: 'Perform routine dependency updates constrained to non-breaking maintenance flows across Python (uv lock refresh), Yarn lock refresh, and container image pulls/builds.'
argument-hint: '[scope: python|frontend|containers|all] [--verify]'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md).

# Dependency Upgrade Safe

## Purpose
- Run low-risk maintenance updates for routine upkeep.
- Refresh lockfiles and image layers without intentionally widening dependency ranges.
- Provide a single command path for regular maintenance cycles.

## Skill Selection (Important)
- Use this skill for patch/minor-oriented maintenance workflows.
- Use this when user asks for regular dependency refreshes.
- Do not use this skill for intentional breaking upgrades.
- For breaking changes and migration planning, use `dependency-upgrade-major`.

## Scopes
- `python`: refresh uv lock state from existing constraints.
- `frontend`: refresh the `webui` Yarn lockfile within existing package.json ranges.
- `containers`: pull/build compose images for updated base layers.
- `all`: run all scopes in order.

## Command
```bash
bash .github/skills/dependency-upgrade-safe/scripts/upgrade_safe.sh all --verify
```

## Execution Notes For Agents
- Run from repository root.
- Use unsandboxed execution if uv or Yarn config paths are blocked.
- This skill does not intentionally widen version ranges in manifest files.
- With `--verify`, run quick checks after updates (Python tests + frontend lint/build + compose config checks).
