#!/bin/sh
# Ensure that database is up to date
alembic upgrade head

# Run container
exec "$@"