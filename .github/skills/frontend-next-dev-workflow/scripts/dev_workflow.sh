#!/usr/bin/env bash
set -euo pipefail

action="${1:-}"

usage() {
  cat <<'EOF'
Usage: dev_workflow.sh <action>

Actions (run in webui/):
  dev-check       Run lint + type-check (fast feedback, no server)
  dev-watch       Start Next.js dev server with hot reload
  test            Run Vitest unit tests (single-run)
  test:watch      Run Vitest in watch mode
  test:coverage   Run Vitest with coverage report
  build-validate  Run lint + type-check + build (pre-commit validation)
  full-check      Run lint + type-check + test + build (comprehensive)
EOF
}

if [ -z "$action" ]; then
  usage
  exit 2
fi

if [ ! -d "webui" ]; then
  echo "Directory not found: webui" >&2
  exit 1
fi

pushd "webui" >/dev/null

dev_check() {
  echo "[frontend-next] Running dev-check (lint + type-check)..."
  yarn lint
  npx tsc --noEmit
  echo "[frontend-next] ✓ dev-check passed"
}

dev_watch() {
  echo "[frontend-next] Starting dev server..."
  yarn dev
}

test_run() {
  echo "[frontend-next] Running tests..."
  yarn test
}

test_watch() {
  echo "[frontend-next] Starting test watch mode..."
  yarn test --watch
}

test_coverage() {
  echo "[frontend-next] Running tests with coverage..."
  yarn test:coverage
}

build_validate() {
  echo "[frontend-next] Running build validation..."
  echo "  - Linting..."
  yarn lint
  echo "  - Type checking..."
  npx tsc --noEmit
  echo "  - Building..."
  yarn build
  echo "[frontend-next] ✓ build-validate passed - production-ready"
}

full_check() {
  echo "[frontend-next] Running full check (lint + type-check + test + build)..."
  echo "  - Linting..."
  yarn lint
  echo "  - Type checking..."
  npx tsc --noEmit
  echo "  - Running tests..."
  yarn test
  echo "  - Building..."
  yarn build
  echo "[frontend-next] ✓ Full check passed - ready to push"
}

case "$action" in
  dev-check)
    dev_check
    ;;
  dev-watch)
    dev_watch
    ;;
  test)
    test_run
    ;;
  test:watch)
    test_watch
    ;;
  test:coverage)
    test_coverage
    ;;
  build-validate)
    build_validate
    ;;
  full-check)
    full_check
    ;;
  *)
    popd >/dev/null
    echo "Invalid action: $action" >&2
    usage
    exit 2
    ;;
esac

popd >/dev/null
