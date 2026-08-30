#!/usr/bin/env bash
set -euo pipefail

scope="${1:-changed}"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but not found in PATH." >&2
  exit 1
fi

run_checks_for_files() {
  local files=("$@")
  if [ ${#files[@]} -eq 0 ]; then
    echo "No changed Python files detected."
    exit 0
  fi

  echo "Running Ruff on ${#files[@]} changed Python file(s)..."
  uv run ruff check "${files[@]}"

  echo "Running ty on ${#files[@]} changed Python file(s)..."
  uv run ty check "${files[@]}"
}

case "$scope" in
  changed)
    changed_files=()
    while IFS= read -r file; do
      [ -n "$file" ] && changed_files+=("$file")
    done < <(
      {
        git diff --name-only --diff-filter=ACMRTUXB -- '*.py'
        git diff --cached --name-only --diff-filter=ACMRTUXB -- '*.py'
        git ls-files --others --exclude-standard -- '*.py'
      } | sort -u
    )
    run_checks_for_files "${changed_files[@]}"
    ;;
  all)
    echo "Running Ruff on full repository..."
    uv run ruff check .

    echo "Running ty on full repository..."
    uv run ty check .
    ;;
  *)
    echo "Usage: $0 [changed|all]" >&2
    exit 2
    ;;
esac
