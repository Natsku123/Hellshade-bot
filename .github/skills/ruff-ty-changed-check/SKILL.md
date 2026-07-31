---
name: ruff-ty-changed-check
description: 'Run Ruff and ty against changed Python files. Use for linting and static type validation before commit or pull request updates. Executes tools with uv run and requires unsandboxed terminal execution.'
argument-hint: '[optional target: changed|all]'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md) for the standard workflow.

# Ruff + ty Changed Check

## Purpose
- Validate linting and static typing for Python code.
- Catch style and type issues quickly before commit/PR.

## Skill Selection (Important)
- Use this skill when the user asks to run lint/type checks ("ruff", "ty", "lint", "type check", "static checks").
- Do not use this skill when the user asks to run tests or verify runtime behavior.
- For test execution, use the `pytest-test-runner` skill in `.github/skills/pytest-test-runner/SKILL.md`.

## When to Use
- Before committing Python changes.
- Before opening or updating a pull request.
- After refactors that may affect linting or typing.

## When Not to Use
- User asks for pytest execution, test failures, regression verification, or coverage reports.
- User asks for live Discord integration test runs.

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
