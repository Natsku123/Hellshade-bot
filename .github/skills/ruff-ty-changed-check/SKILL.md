---
name: ruff-ty-changed-check
description: 'Run Ruff and ty against changed Python files. Use when validating local edits before commit, pull request updates, or quick regression checks. Executes tools with uv run and requires unsandboxed terminal execution.'
argument-hint: '[optional target: changed|all]'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md) for the standard workflow.

# Ruff + ty Changed Check

## When to Use
- Before committing Python changes.
- Before opening or updating a pull request.
- After refactors that may affect linting or typing.

## Requirements
- Run terminal commands outside the sandbox.
- Use `uv run` for both tools.
- Prefer `uv sync --dev` to prepare the environment when needed.
- Avoid direct `.venv/bin/python`, `pip`, `ruff`, or `ty` invocations when `uv run` can be used instead.
- If the sandbox blocks the uv virtualenv or cache paths, treat that as a reason to rerun the check outside the sandbox rather than falling back to direct Python binaries.

## Procedure
1. Decide scope:
- `changed` (default): check only changed Python files.
- `all`: check the entire repository.
2. Run the script [scripts/check_changed.sh](./scripts/check_changed.sh) with the selected scope.
3. If any check fails, fix issues and rerun until both pass.

## Command Examples
```bash
# Changed files only
bash .github/skills/ruff-ty-changed-check/scripts/check_changed.sh changed

# Full repository
bash .github/skills/ruff-ty-changed-check/scripts/check_changed.sh all
```

## Execution Notes For Agents
- Use `run_in_terminal` with `mode: "sync"`.
- Set `requestUnsandboxedExecution: true`.
- Keep commands in repo root so relative paths resolve correctly.
- When the environment is missing, run `uv sync --dev` first, then execute checks with `uv run`.
