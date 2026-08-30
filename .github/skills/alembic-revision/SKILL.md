---
name: alembic-revision
description: 'Create and review Alembic database revisions from SQLAlchemy model changes. Use when adding, changing, or removing persistent database schema.'
argument-hint: '<revision message>'
---

> Repository rule: always use the uv-managed environment for Python commands in this workspace. Follow [.github/copilot-instructions.md](../../copilot-instructions.md).

# Alembic Revision

## Purpose
- Generate a candidate Alembic revision from the current SQLAlchemy models.
- Check the revision chain after generation.
- Keep schema review and database application as separate, explicit steps.

## Use This Skill When
- Adding, changing, or removing a database table, column, index, constraint, or relationship.
- Creating a migration for a changed SQLAlchemy model.

## Do Not Use This Skill When
- Applying an existing revision only; use `uv run alembic upgrade head`.
- Making data-only corrections that do not require a schema revision.

## Prerequisites
- Run from the repository root.
- Configure a reachable database using the application's database settings.
- Ensure the target database is at the current Alembic head before generating a revision.
- For the Compose database, start it first with `docker compose up -d db`.

## Command

```bash
bash .github/skills/alembic-revision/scripts/create_revision.sh "describe schema change"
```

For example:

```bash
bash .github/skills/alembic-revision/scripts/create_revision.sh "add gw2 tp orders"
```

## Required Review

1. Inspect the generated file in `alembic/versions/` and confirm both `upgrade()` and `downgrade()` are correct.
2. Check that unintended model differences were not included.
3. Apply the reviewed revision to a disposable or development database:

```bash
uv run alembic upgrade head
```

4. Run the relevant tests before committing the model and revision together.

## Execution Notes For Agents
- Autogeneration produces a candidate, not an approved migration. Never apply an unreviewed generated revision to production.
- Use unsandboxed execution if `uv` cannot access its managed cache.
- Do not create an empty revision for model changes unless the migration requires hand-written SQL.