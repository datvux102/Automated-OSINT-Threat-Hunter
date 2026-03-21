#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

echo "==> Building frontend"
npm -C frontend run build >/dev/null

echo "==> Starting backend bridge on port ${BACKEND_PORT}"
PYTHONPYCACHEPREFIX="$ROOT_DIR/.pycacheprefix" PYTHONPATH=src "$PYTHON_BIN" -m cybersentinel.dev_server >/tmp/cybersentinel-backend.log 2>&1 &
BACKEND_PID=$!

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if ! curl -fsS "http://127.0.0.1:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
  echo "Backend failed to start. Log:"
  sed -n '1,120p' /tmp/cybersentinel-backend.log
  exit 1
fi

echo "==> Running API smoke tests"
"$PYTHON_BIN" scripts/smoke_e2e.py "http://127.0.0.1:${BACKEND_PORT}"

echo "==> Production-like E2E check completed"

