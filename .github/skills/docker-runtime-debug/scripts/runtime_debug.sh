#!/usr/bin/env bash
set -euo pipefail

stack="${1:-}"
check="${2:-overview}"
service="${3:-}"

usage() {
  cat <<'EOF'
Usage: runtime_debug.sh <stack> [check] [service]

Checks:
  overview   ps + recent logs snapshot
  health     health status summary
  db         postgres readiness diagnostics
  traefik    traefik logs + HTTP probes
  logs       follow logs (all services or one service)
EOF
}

if [ -z "$stack" ]; then
  usage
  exit 2
fi

case "$stack" in
  dev) compose_file="docker-compose-dev.yml" ;;
  next) compose_file="docker-compose-next.yml" ;;
  *)
    echo "Invalid stack: $stack" >&2
    usage
    exit 2
    ;;
esac

compose_cmd=(docker compose -f "$compose_file")
if ! docker compose version >/dev/null 2>&1; then
  if command -v docker-compose >/dev/null 2>&1; then
    compose_cmd=(docker-compose -f "$compose_file")
  else
    echo "Neither 'docker compose' nor 'docker-compose' is available." >&2
    exit 1
  fi
fi

container_ids=()
while IFS= read -r cid; do
  [ -n "$cid" ] && container_ids+=("$cid")
done < <("${compose_cmd[@]}" ps -q)

case "$check" in
  overview)
    "${compose_cmd[@]}" ps
    echo
    echo "Recent logs (last 80 lines):"
    "${compose_cmd[@]}" logs --tail 80 || true
    ;;
  health)
    "${compose_cmd[@]}" ps
    echo
    if [ ${#container_ids[@]} -eq 0 ]; then
      echo "No containers found for stack '$stack'."
      exit 0
    fi
    for cid in "${container_ids[@]}"; do
      name="$(docker inspect --format '{{.Name}}' "$cid" | sed 's#^/##')"
      status="$(docker inspect --format '{{.State.Status}}' "$cid")"
      health_status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' "$cid")"
      echo "$name status=$status health=$health_status"
    done
    ;;
  db)
    "${compose_cmd[@]}" ps db || true
    echo
    "${compose_cmd[@]}" logs --tail 120 db || true
    echo
    "${compose_cmd[@]}" exec db sh -lc 'pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}"'
    ;;
  traefik)
    "${compose_cmd[@]}" ps traefik || true
    echo
    "${compose_cmd[@]}" logs --tail 200 traefik || true
    echo
    if command -v curl >/dev/null 2>&1; then
      echo "HTTP probe: localhost"
      curl -sS -I http://localhost/ || true
      echo
      echo "HTTP probe: bot.localhost"
      curl -sS -I http://bot.localhost/ || true
    else
      echo "curl not available; skipping HTTP probe"
    fi
    ;;
  logs)
    if [ -n "$service" ]; then
      "${compose_cmd[@]}" logs -f "$service"
    else
      "${compose_cmd[@]}" logs -f
    fi
    ;;
  *)
    echo "Invalid check: $check" >&2
    usage
    exit 2
    ;;
esac
