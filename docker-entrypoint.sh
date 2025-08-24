#!/usr/bin/env bash
# Ensure that database is up to date
uv run alembic upgrade head

# Run container
exec "$@"