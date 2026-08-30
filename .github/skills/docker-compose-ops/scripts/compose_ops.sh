#!/usr/bin/env bash
set -euo pipefail

stack="${1:-}"
action="${2:-}"
service="${3:-}"

usage() {
  cat <<'EOF'
Usage: compose_ops.sh <stack> <action> [service]

Stacks:
  dev    -> docker-compose-dev.yml
  webui  -> docker-compose.yml

Actions:
  up        Bring stack up in detached mode
  down      Stop and remove stack resources
  restart   Restart all services or a single service
  ps        Show container status
  logs      Follow logs for all services or one service
  build     Build all services or one service
  pull      Pull service images
  config    Render merged compose config
EOF
}

if [ -z "$stack" ] || [ -z "$action" ]; then
  usage
  exit 2
fi

case "$stack" in
  dev) compose_file="docker-compose-dev.yml" ;;
  webui) compose_file="docker-compose.yml" ;;
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

case "$action" in
  up)
    "${compose_cmd[@]}" up -d ${service:+"$service"}
    ;;
  down)
    "${compose_cmd[@]}" down
    ;;
  restart)
    "${compose_cmd[@]}" restart ${service:+"$service"}
    ;;
  ps)
    "${compose_cmd[@]}" ps
    ;;
  logs)
    if [ -n "$service" ]; then
      "${compose_cmd[@]}" logs -f "$service"
    else
      "${compose_cmd[@]}" logs -f
    fi
    ;;
  build)
    "${compose_cmd[@]}" build ${service:+"$service"}
    ;;
  pull)
    "${compose_cmd[@]}" pull ${service:+"$service"}
    ;;
  config)
    "${compose_cmd[@]}" config
    ;;
  *)
    echo "Invalid action: $action" >&2
    usage
    exit 2
    ;;
esac
