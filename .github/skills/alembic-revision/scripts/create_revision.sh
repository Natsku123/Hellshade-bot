#!/usr/bin/env bash
set -euo pipefail

message="${1:-}"

usage() {
  cat <<'EOF'
Usage: create_revision.sh "revision message"

Generates an Alembic revision from the current SQLAlchemy models and displays
the current migration heads. Review the generated revision before applying it.
EOF
}

if [ -z "$message" ]; then
  usage >&2
  exit 2
fi

if [ ! -f "alembic.ini" ] || [ ! -d "alembic/versions" ]; then
  echo "Run this command from the repository root." >&2
  exit 1
fi

uv run alembic revision --autogenerate -m "$message"
uv run alembic heads