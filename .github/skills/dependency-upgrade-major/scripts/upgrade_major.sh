#!/usr/bin/env bash
set -euo pipefail

scope="${1:-all}"
phase="${2:-plan}"
verify="${3:-}"

usage() {
  cat <<'EOF'
Usage: upgrade_major.sh [scope] [phase] [--verify]

Scopes:
  python
  frontend
  containers
  all

Phases:
  plan   Collect major-upgrade candidates and changelog links only
  apply  Execute staged major-upgrade commands
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

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for changelog metadata parsing." >&2
  exit 1
fi

fetch_python_meta() {
  local package="$1"
  local url="https://pypi.org/pypi/${package}/json"

  echo "Package: $package"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" | jq -r '
      "Latest: " + (.info.version // "unknown"),
      "Project URL: " + (.info.project_url // .info.home_page // "n/a"),
      "Release URLs:",
      (.info.project_urls // {} | to_entries[]? | "  - " + .key + ": " + .value)
    '
  else
    echo "curl not available; cannot fetch $url"
  fi
  echo
}

fetch_node_meta() {
  local package="$1"
  echo "Package: $package"
  if command -v yarn >/dev/null 2>&1; then
    yarn npm info "$package" --json 2>/dev/null | jq -r '
      if type == "array" then .[0] else . end |
      "Latest: " + ((.data["dist-tags"].latest // .version // "unknown")|tostring),
      "Homepage: " + (.data.homepage // "n/a"),
      "Repository: " + ((.data.repository.url // .data.repository // "n/a")|tostring)
    ' || true
  elif command -v npm >/dev/null 2>&1; then
    npm view "$package" version homepage repository.url 2>/dev/null || true
  else
    echo "Neither yarn nor npm is available for node metadata lookup"
  fi
  echo
}

python_plan() {
  echo "[major][plan] Python package metadata"
  fetch_python_meta "alembic"
  fetch_python_meta "sqlalchemy"
  fetch_python_meta "nextcord"
}

frontend_plan() {
  echo "[major][plan] Node package metadata"
  fetch_node_meta "next"
  fetch_node_meta "react"
  fetch_node_meta "pg"
}

containers_plan() {
  echo "[major][plan] Container image surface"
  echo "Inspect Dockerfiles for base tags before major updates:"
  echo "  - Dockerfile"
  echo "  - webui/Dockerfile"
  echo
}

python_apply() {
  echo "[major][apply] Upgrading direct Python dependencies (manual pyproject edits may be required)"
  echo "Recommended staged approach: edit one dependency group at a time, then run uv lock and tests"
  uv lock --upgrade
}

frontend_apply() {
  echo "[major][apply] Running interactive webui upgrades"
  bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh upgrade-interactive
}

containers_apply() {
  echo "[major][apply] Pull/build container images after base-tag updates"
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev pull || true
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui pull || true
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh dev build
  bash .github/skills/docker-compose-ops/scripts/compose_ops.sh webui build
}

run_verify() {
  echo "[major] Running checkpoint verification"
  make test-fast
  bash .github/skills/yarn-frontend-manager/scripts/yarn_frontend.sh lint
  bash .github/skills/docker-runtime-debug/scripts/runtime_debug.sh webui health
}

run_scope_phase() {
  local chosen_scope="$1"
  local chosen_phase="$2"

  case "$chosen_scope" in
    python)
      if [ "$chosen_phase" = "plan" ]; then
        python_plan
      else
        python_apply
      fi
      ;;
    frontend)
      if [ "$chosen_phase" = "plan" ]; then
        frontend_plan
      else
        frontend_apply
      fi
      ;;
    containers)
      if [ "$chosen_phase" = "plan" ]; then
        containers_plan
      else
        containers_apply
      fi
      ;;
    all)
      run_scope_phase python "$chosen_phase"
      run_scope_phase frontend "$chosen_phase"
      run_scope_phase containers "$chosen_phase"
      ;;
    *)
      echo "Invalid scope: $chosen_scope" >&2
      usage
      exit 2
      ;;
  esac
}

case "$phase" in
  plan|apply) ;;
  *)
    echo "Invalid phase: $phase" >&2
    usage
    exit 2
    ;;
esac

run_scope_phase "$scope" "$phase"

if [ "$verify" = "--verify" ]; then
  run_verify
elif [ -n "$verify" ]; then
  echo "Unknown option: $verify" >&2
  usage
  exit 2
fi

echo "[major] Workflow complete. If compatibility failures occurred, keep changes in small batches and iterate fixes before continuing."
