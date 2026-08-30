#!/usr/bin/env bash
set -euo pipefail

action="${1:-}"

usage() {
  cat <<'EOF'
Usage: yarn_frontend.sh <action>

Actions (run in webui/):
  install
  dev
  build
  lint
  type-check
  test
  test:ui
  test:coverage
  audit
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

if [ -z "$action" ]; then
  usage
  exit 2
fi

if [ ! -d "webui" ]; then
  echo "Directory not found: webui" >&2
  exit 1
fi

pushd "webui" >/dev/null

case "$action" in
  install)
    yarn install --ignore-engines
    ;;
  dev)
    yarn dev
    ;;
  build)
    yarn build
    ;;
  lint)
    yarn lint
    ;;
  type-check)
    npx tsc --noEmit
    ;;
  test)
    yarn test
    ;;
  test:ui)
    yarn test:ui
    ;;
  test:coverage)
    yarn test:coverage
    ;;
  audit)
    yarn audit || true
    ;;
  outdated)
    yarn outdated || true
    ;;
  upgrade-safe)
    yarn upgrade
    ;;
  upgrade-interactive)
    yarn upgrade-interactive --latest
    ;;
  dedupe)
    yarn install
    ;;
  *)
    popd >/dev/null
    echo "Invalid action: $action" >&2
    usage
    exit 2
    ;;
esac

popd >/dev/null
