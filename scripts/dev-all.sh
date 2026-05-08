#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "${web_pid:-}" ]]; then
    kill "$web_pid" 2>/dev/null || true
  fi
  if [[ -n "${transcript_worker_pid:-}" ]]; then
    kill "$transcript_worker_pid" 2>/dev/null || true
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
docker-compose up -d postgres redis meilisearch

echo "[recall] applying database migrations"
cd "$API_DIR"
alembic upgrade head

echo "[recall] starting api"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
api_pid=$!

echo "[recall] starting ingestion worker"
rq worker recall-ingestion --url redis://localhost:6379/0 &
worker_pid=$!

echo "[recall] starting transcript worker"
rq worker recall-transcripts --url redis://localhost:6379/0 &
transcript_worker_pid=$!

echo "[recall] starting web"
cd "$ROOT_DIR/apps/web"
pnpm dev &
web_pid=$!

echo "[recall] running on http://localhost:3000 and http://localhost:8000"
wait "$api_pid" "$worker_pid" "$transcript_worker_pid" "$web_pid"