#!/usr/bin/env bash
set -euo pipefail

app="${1:-}"
action="${2:-}"

usage() {
  cat <<'EOF'
Usage: yarn_frontend.sh <app> <action>

Apps:
  frontend  Legacy Vue frontend
  next      Next.js frontend-next
  all       Run action on both apps

Actions:
  install
  dev
  build
  lint
  outdated
  upgrade-safe
  upgrade-interactive
  dedupe
EOF
}

if ! command -v yarn >/dev/null 2>&1; then
  echo "yarn is required but not found in PATH." >&2
  exit 1
fi

if [ -z "$app" ] || [ -z "$action" ]; then
  usage
  exit 2
fi

run_action() {
  local dir="$1"

  if [ ! -d "$dir" ]; then
    echo "Directory not found: $dir" >&2
    exit 1
  fi

  pushd "$dir" >/dev/null

  case "$action" in
    install)
      if [ "$dir" = "frontend-next" ]; then
        yarn install --ignore-engines
      else
        yarn install
      fi
      ;;
    dev)
      if [ "$dir" = "frontend-next" ]; then
        yarn dev
      else
        yarn serve
      fi
      ;;
    build)
      yarn build
      ;;
    lint)
      if [ "$dir" = "frontend" ]; then
        yarn lint
      else
        yarn lint
      fi
      ;;
    outdated)
      yarn outdated || true
      ;;
    upgrade-safe)
      if [ "$dir" = "frontend-next" ]; then
        yarn upgrade
      else
        yarn up -R
      fi
      ;;
    upgrade-interactive)
      if [ "$dir" = "frontend-next" ]; then
        yarn upgrade-interactive --latest
      else
        yarn up -i
      fi
      ;;
    dedupe)
      if [ "$dir" = "frontend-next" ]; then
        yarn install
      else
        yarn dedupe
      fi
      ;;
    *)
      popd >/dev/null
      echo "Invalid action: $action" >&2
      usage
      exit 2
      ;;
  esac

  popd >/dev/null
}

case "$app" in
  frontend)
    run_action "frontend"
    ;;
  next)
    run_action "frontend-next"
    ;;
  all)
    run_action "frontend"
    run_action "frontend-next"
    ;;
  *)
    echo "Invalid app: $app" >&2
    usage
    exit 2
    ;;
esac
