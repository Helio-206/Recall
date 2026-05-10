#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
PYTHON_BIN="${PYTHON_BIN:-$API_DIR/.venv/bin/python}"

# Resolve a usable Python binary if the provided/default path is missing.
if [[ ! -x "$PYTHON_BIN" ]]; then
  for candidate in \
    "$API_DIR/.venv/bin/python" \
    "$ROOT_DIR/.venv/bin/python" \
    "$(cd "$ROOT_DIR/.." && pwd)/.venv/bin/python" \
    "$(command -v python3 || true)" \
    "$(command -v python || true)"
  do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "[recall] error: no usable Python interpreter found."
  echo "[recall] set PYTHON_BIN to a valid path, e.g. /path/to/.venv/bin/python"
  exit 1
fi

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "${web_pid:-}" ]]; then
    kill "$web_pid" 2>/dev/null || true
  fi
  if [[ -n "${transcript_worker_pid:-}" ]]; then
    kill "$transcript_worker_pid" 2>/dev/null || true
  fi
  if [[ -n "${ai_worker_pid:-}" ]]; then
    kill "$ai_worker_pid" 2>/dev/null || true
  fi
  if [[ -n "${curriculum_worker_pid:-}" ]]; then
    kill "$curriculum_worker_pid" 2>/dev/null || true
  fi
  if [[ -n "${worker_pid:-}" ]]; then
    kill "$worker_pid" 2>/dev/null || true
  fi
  if [[ -n "${api_pid:-}" ]]; then
    kill "$api_pid" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

find_listening_pids() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
    return
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :$port" 2>/dev/null \
      | awk -F 'pid=' 'NR > 1 {split($2, a, ","); if (a[1] ~ /^[0-9]+$/) print a[1]}' \
      | sort -u || true
    return
  fi

  return 0
}

free_port_if_needed() {
  local port="$1"
  local label="$2"
  local pids

  pids="$(find_listening_pids "$port" | tr '\n' ' ' | xargs 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return
  fi

  echo "[recall] freeing port $port used by $label (pids: $pids)"
  kill $pids 2>/dev/null || true

  local attempts=0
  while [[ $attempts -lt 10 ]]; do
    if [[ -z "$(find_listening_pids "$port")" ]]; then
      return
    fi
    attempts=$((attempts + 1))
    sleep 0.3
  done

  local stubborn
  stubborn="$(find_listening_pids "$port" | tr '\n' ' ' | xargs 2>/dev/null || true)"
  if [[ -n "$stubborn" ]]; then
    echo "[recall] forcing shutdown on port $port (pids: $stubborn)"
    kill -9 $stubborn 2>/dev/null || true
  fi
}

pick_available_port() {
  local preferred_port="$1"
  local selected_port

  selected_port="$(
    "$PYTHON_BIN" - "$preferred_port" <<'PY'
import socket
import sys

start_port = int(sys.argv[1])

def can_bind_ipv4(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()

def can_bind_ipv6(port: int) -> bool:
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    except OSError:
        return True

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        sock.bind(("::", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()

for port in range(start_port, start_port + 200):
    if can_bind_ipv4(port) and can_bind_ipv6(port):
        print(port)
        raise SystemExit(0)

raise SystemExit(1)
PY
  )"

  if [[ -z "$selected_port" ]]; then
    echo "[recall] error: unable to find a free port starting from $preferred_port"
    exit 1
  fi

  echo "$selected_port"
}

cd "$ROOT_DIR"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

free_port_if_needed "$API_PORT" "api"
free_port_if_needed "$WEB_PORT" "web"

resolved_api_port="$(pick_available_port "$API_PORT")"
resolved_web_port="$(pick_available_port "$WEB_PORT")"

if [[ "$resolved_api_port" != "$API_PORT" ]]; then
  echo "[recall] api port $API_PORT unavailable, using $resolved_api_port"
fi
if [[ "$resolved_web_port" != "$WEB_PORT" ]]; then
  echo "[recall] web port $WEB_PORT unavailable, using $resolved_web_port"
fi

API_PORT="$resolved_api_port"
WEB_PORT="$resolved_web_port"

export BACKEND_CORS_ORIGINS="${BACKEND_CORS_ORIGINS:-http://localhost:${WEB_PORT},http://127.0.0.1:${WEB_PORT}}"

echo "[recall] starting infra containers"
docker-compose up -d --no-recreate postgres redis meilisearch

postgres_port="${POSTGRES_PORT:-$(docker-compose port postgres 5432 | awk -F: 'END {print $NF}')}"
postgres_port="${postgres_port//[[:space:]]/}"

export POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
export POSTGRES_PORT="$postgres_port"
export POSTGRES_USER="${POSTGRES_USER:-recall}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-recall}"
export POSTGRES_DB="${POSTGRES_DB:-recall}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}}"

echo "[recall] applying database migrations"
cd "$API_DIR"
"$PYTHON_BIN" -m alembic upgrade head

echo "[recall] starting api"
"$PYTHON_BIN" -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$API_PORT" &
api_pid=$!

echo "[recall] starting ingestion worker"
"$PYTHON_BIN" -m rq worker recall-ingestion --url redis://localhost:6379/0 &
worker_pid=$!

echo "[recall] starting transcript worker"
"$PYTHON_BIN" -m rq worker recall-transcripts --url redis://localhost:6379/0 &
transcript_worker_pid=$!

echo "[recall] starting ai worker"
"$PYTHON_BIN" -m rq worker ai-summary --url redis://localhost:6379/0 &
ai_worker_pid=$!

echo "[recall] starting curriculum worker"
"$PYTHON_BIN" -m rq worker curriculum-reconstruction --url redis://localhost:6379/0 &
curriculum_worker_pid=$!

echo "[recall] starting web"
cd "$ROOT_DIR/apps/web"
rm -rf .next
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${API_PORT}/api/v1}" PORT="$WEB_PORT" pnpm dev &
web_pid=$!

echo "[recall] running on http://localhost:$WEB_PORT and http://localhost:$API_PORT"
wait \
  "$api_pid" \
  "$worker_pid" \
  "$transcript_worker_pid" \
  "$ai_worker_pid" \
  "$curriculum_worker_pid" \
  "$web_pid"
