---
name: frontend-next-dev-workflow
description: 'Manage frontend-next dev workflow with combined dev/lint/type-check operations, test execution, and build validation.'
argument-hint: '[action: dev-check|dev-watch|test|test:watch|test:coverage|build-validate|full-check]'
---

> Repository rule: always use the Yarn-managed webui environment for this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md).

# Frontend Next Dev Workflow

## Purpose
- Streamline frontend Next.js development cycles with combined validation steps.
- Provide quick feedback loops for styling, components, and API routes.
- Catch type errors, lint issues, and test failures early before commits.

## Skill Selection (Important)
- Use this skill for frontend Next.js development, testing, and build validation.
- Use this when working on webui components, API routes, styling, or pages.
- Use this for pre-commit validation and CI-like checks locally.
- For package management and dependency upgrades, use `yarn-frontend-manager`.
- For Docker or backend work, use dedicated skills.

## App
- `webui` -> Next.js app, TypeScript, Tailwind CSS, Vitest, ESLint.

## Actions
- `dev-check`: Run lint + type-check without starting dev server (fast feedback).
- `dev-watch`: Start Next.js dev server with hot reload.
- `test`: Run Vitest unit tests in single-run mode.
- `test:watch`: Run Vitest tests in watch mode (continuous).
- `test:coverage`: Run Vitest with coverage report.
- `build-validate`: Run lint + type-check + build to validate production-ready code.
- `full-check`: Run lint + type-check + test + build (comprehensive pre-push validation).

## Workflow
1. During development: Use `dev-watch` for local iteration, `dev-check` for quick validation.
2. Before commit: Use `build-validate` to ensure build-ready code.
3. Before push: Use `full-check` for comprehensive validation.

## Command
```bash
bash .github/skills/frontend-next-dev-workflow/scripts/dev_workflow.sh dev-check
bash .github/skills/frontend-next-dev-workflow/scripts/dev_workflow.sh dev-watch
bash .github/skills/frontend-next-dev-workflow/scripts/dev_workflow.sh test
bash .github/skills/frontend-next-dev-workflow/scripts/dev_workflow.sh full-check
```

## Execution Notes For Agents
- Run from repository root.
- For `dev-watch`, prefer async mode because the dev server is long-running.
- For validation actions, use sync mode.
- Type checking requires TypeScript to be installed (`yarn install` first).
- Tests require dependencies (`yarn install` first) and only run successfully if tests are properly configured.
