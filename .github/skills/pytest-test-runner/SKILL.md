---
name: pytest-test-runner
description: 'Run repository tests with uv/pytest and Make targets. Use for runtime validation, regression checks, and coverage runs, including optional live Discord test execution.'
argument-hint: '[optional target: fast|full|live|live-enabled|cov|cov-dispatch|cov-all|file::<path>|node::<pytest node id>]'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md) for the standard workflow.

# Pytest Test Runner

## Purpose
- Execute repository tests for behavioral validation.
- Reproduce and verify test failures.
- Run coverage-enabled test suites.

## Skill Selection (Important)
- Use this skill when the user asks to run tests, verify fixes, check regressions, or produce coverage.
- Use this skill after code edits that could affect runtime behavior.
- Do not use this skill for lint/type-only requests.
- For lint/type checks, use `ruff-ty-changed-check` in `.github/skills/ruff-ty-changed-check/SKILL.md`.

## When to Use
- "Run tests" or "run pytest" requests.
- "Make sure everything still passes" after edits.
- Coverage requests (for example "run all with coverage").
- Live Discord test execution requests.

## When Not to Use
- User requests only style/type validation (ruff/ty).
- User requests non-Python tooling checks unrelated to pytest.

## Prerequisites
- Run from repository root.
- Use `uv run` commands (or `make` targets that wrap `uv run`).
- If dependencies are missing, run `uv sync` (or `uv sync --dev`).
- If sandbox blocks uv paths, rerun outside sandbox.

## Standard Commands
```bash
# Full default suite (live tests remain skipped)
make test

# Fast local suites
make test-fast

# Dispatch suite only
make test-dispatch

# Regression/meta suite only
make test-regression

# Helper/unit utilities only
make test-utils

# Select live tests only (still skipped unless enabled)
make test-live

# Explicitly enable live Discord tests
make test-live-enabled

# Full suite with coverage summary
make test-cov

# Focused coverage suite for dispatch/regression/helpers/config
make test-cov-dispatch

# Full coverage plus XML output
make test-cov-all
```

## Optional Target Mapping
- `fast` -> `make test-fast`
- `full` -> `make test`
- `live` -> `make test-live`
- `live-enabled` -> `make test-live-enabled`
- `cov` -> `make test-cov`
- `cov-dispatch` -> `make test-cov-dispatch`
- `cov-all` -> `make test-cov-all`
- `file::<path>` -> `uv run pytest <path>`
- `node::<pytest node id>` -> `uv run pytest <node id>`

## Live Test Requirements
- `TOKEN` (or `BOT_TOKEN`) must be configured.
- `TEST_GUILD_ID` must be configured.
- Use `--run-live` (already wrapped by `make test-live-enabled`).

## Execution Notes For Agents
- Use `run_in_terminal` with `mode: "sync"`.
- Prefer make targets first for consistency.
- For all success claims, include fresh test output evidence.
- If a test command fails, report the failing tests and propose/run the next focused command.
