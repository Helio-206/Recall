#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
PYTHON_BIN="${PYTHON_BIN:-/home/helio/HEr/.venv/bin/python}"

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

cd "$ROOT_DIR"

echo "[recall] starting infra containers"
docker-compose up -d --no-recreate postgres redis meilisearch

postgres_port="${POSTGRES_PORT:-$(docker-compose port postgres 5432 | awk -F: 'END {print $NF}') }"
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
"$PYTHON_BIN" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
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
pnpm dev &
web_pid=$!

echo "[recall] running on http://localhost:3000 and http://localhost:8000"
wait \
  "$api_pid" \
  "$worker_pid" \
  "$transcript_worker_pid" \
  "$ai_worker_pid" \
  "$curriculum_worker_pid" \
  "$web_pid"