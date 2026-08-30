#!/usr/bin/env bash
set -euo pipefail

scope="${1:-all}"
verify="${2:-}"

usage() {
  cat <<'EOF'
Usage: upgrade_safe.sh [scope] [--verify]

Scopes:
  python
  frontend
  containers
  all
EOF
}

if [ "$scope" = "-h" ] || [ "$scope" = "--help" ]; then
  usage
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but not found in PATH." >&2
  exit 1
fi

run_python() {
  echo "[safe] Refreshing Python lockfile from existing constraints"
  uv lock --upgrade
}

run_frontend() {
  echo "[safe] Refreshing webui lockfile within declared semver ranges"
  bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh upgrade-safe
}

run_containers() {
  echo "[safe] Pulling and building compose stacks"
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev pull || true
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui pull || true
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev build
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui build
}

run_verify() {
  echo "[safe] Running verification checks"
  make test-fast
  bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh lint
  bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh build
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev config >/dev/null
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui config >/dev/null
}

case "$scope" in
  python)
    run_python
    ;;
  frontend)
    run_frontend
    ;;
  containers)
    run_containers
    ;;
  all)
    run_python
    run_frontend
    run_containers
    ;;
  *)
    echo "Invalid scope: $scope" >&2
    usage
    exit 2
    ;;
esac

if [ "$verify" = "--verify" ]; then
  run_verify
elif [ -n "$verify" ]; then
  echo "Unknown option: $verify" >&2
  usage
  exit 2
fi

echo "[safe] Upgrade workflow completed. Review lockfile and image changes before commit."
