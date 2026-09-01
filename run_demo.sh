#!/usr/bin/env bash

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_INPUT="${1:-}"

usage() {
  cat <<'EOF'
Usage: ./run_demo.sh <project>

Projects:
  0 or 00  Dynamic Todo Workspace
  1 or 01  NYC Taxi Trip-Duration Prediction
  2 or 02  Nano LLM Transformer
  3 or 03  Customer Segmentation Clustering
  4 or 04  Associative Pattern Mining
  5 or 05  Data Science Skills Lab

The first run creates a shared Python environment and installs missing client
dependencies. Later runs start immediately. Press Ctrl-C once to stop both the
FastAPI server and React client.

Set DEMO_NO_OPEN=1 to prevent the script from opening the browser automatically.
Set DEMO_PYTHON=/path/to/python3.12 to choose a Python interpreter explicitly.
EOF
}

case "$PROJECT_INPUT" in
  -h|--help) usage; exit 0 ;;
  0|00) PROJECT_ID="00"; PROJECT_DIR="00_dynamic_todo_workspace"; API_WORKDIR="server"; API_APP="main:app"; API_PORT="8000"; CLIENT_PORT="5173" ;;
  1|01) PROJECT_ID="01"; PROJECT_DIR="01_nyc_taxi_trip_prediction"; API_WORKDIR="."; API_APP="server.main:app"; API_PORT="8001"; CLIENT_PORT="5173" ;;
  2|02) PROJECT_ID="02"; PROJECT_DIR="02_nano_llm_transformer"; API_WORKDIR="server"; API_APP="main:app"; API_PORT="8002"; CLIENT_PORT="5175" ;;
  3|03) PROJECT_ID="03"; PROJECT_DIR="03_customer_segmentation_clustering"; API_WORKDIR="."; API_APP="server.app:app"; API_PORT="8003"; CLIENT_PORT="5173" ;;
  4|04) PROJECT_ID="04"; PROJECT_DIR="04_associative_pattern_mining"; API_WORKDIR="."; API_APP="server.main:app"; API_PORT="8004"; CLIENT_PORT="5173" ;;
  5|05) PROJECT_ID="05"; PROJECT_DIR="05_data_science_skills_lab"; API_WORKDIR="."; API_APP="server.main:app"; API_PORT="8005"; CLIENT_PORT="5175" ;;
  *) usage; exit 2 ;;
esac

PROJECT_ROOT="$REPO_ROOT/$PROJECT_DIR"
CLIENT_DIR="$PROJECT_ROOT/client"
VENV_DIR="$REPO_ROOT/.demo-venv"
DEMO_REQUIREMENTS="$REPO_ROOT/scripts/demo-requirements.txt"
REQUIREMENTS_MARKER="$VENV_DIR/.demo-requirements.sha256"

for command_name in npm curl; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
done

if [[ -n "${DEMO_PYTHON:-}" ]]; then
  BOOTSTRAP_PYTHON="$DEMO_PYTHON"
elif command -v python3.12 >/dev/null 2>&1; then
  BOOTSTRAP_PYTHON="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
  BOOTSTRAP_PYTHON="$(command -v python3)"
else
  echo "Python 3 is required. Python 3.12 is recommended." >&2
  exit 1
fi

hash_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

REQUIREMENTS_HASH="$(hash_file "$DEMO_REQUIREMENTS")"
INSTALLED_HASH=""
if [[ -f "$REQUIREMENTS_MARKER" ]]; then
  INSTALLED_HASH="$(<"$REQUIREMENTS_MARKER")"
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "[setup] Creating shared Python environment with $BOOTSTRAP_PYTHON"
  "$BOOTSTRAP_PYTHON" -m venv "$VENV_DIR"
fi

if [[ "$INSTALLED_HASH" != "$REQUIREMENTS_HASH" ]]; then
  echo "[setup] Installing shared demo API/data-science dependencies"
  "$VENV_DIR/bin/python" -m pip install -r "$DEMO_REQUIREMENTS"
  printf '%s\n' "$REQUIREMENTS_HASH" > "$REQUIREMENTS_MARKER"
fi

if [[ ! -x "$CLIENT_DIR/node_modules/.bin/vite" ]]; then
  echo "[setup] Installing Project $PROJECT_ID client dependencies"
  (cd "$CLIENT_DIR" && npm ci)
fi

port_is_busy() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    return 1
  fi
}

for port in "$API_PORT" "$CLIENT_PORT"; do
  if port_is_busy "$port"; then
    echo "Port $port is already in use. Stop the existing demo and retry." >&2
    exit 1
  fi
done

LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/cmpe255-demo-${PROJECT_ID}.XXXXXX")"
API_LOG="$LOG_DIR/api.log"
CLIENT_LOG="$LOG_DIR/client.log"
API_PID=""
CLIENT_PID=""

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  if [[ -n "$CLIENT_PID" ]] && kill -0 "$CLIENT_PID" >/dev/null 2>&1; then
    kill "$CLIENT_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" >/dev/null 2>&1; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi

  [[ -n "$CLIENT_PID" ]] && wait "$CLIENT_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true

  rm -f -- "$API_LOG" "$CLIENT_LOG"
  rmdir "$LOG_DIR" 2>/dev/null || true
  echo
  echo "Project $PROJECT_ID stopped."
  exit "$exit_code"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[start] Project $PROJECT_ID — $PROJECT_DIR"
(
  cd "$PROJECT_ROOT/$API_WORKDIR"
  exec "$VENV_DIR/bin/python" -m uvicorn "$API_APP" --host 127.0.0.1 --port "$API_PORT"
) >"$API_LOG" 2>&1 &
API_PID=$!

(
  cd "$CLIENT_DIR"
  exec "$CLIENT_DIR/node_modules/.bin/vite" --host 127.0.0.1 --port "$CLIENT_PORT"
) >"$CLIENT_LOG" 2>&1 &
CLIENT_PID=$!

wait_for_url() {
  local url="$1"
  local label="$2"
  local process_id="$3"
  local log_file="$4"
  local attempt

  for attempt in $(seq 1 90); do
    if curl --silent --fail --max-time 1 "$url" >/dev/null 2>&1; then
      return 0
    fi
    if ! kill -0 "$process_id" >/dev/null 2>&1; then
      echo "$label stopped before becoming ready:" >&2
      tail -n 30 "$log_file" >&2 || true
      return 1
    fi
    sleep 1
  done

  echo "$label did not become ready within 90 seconds:" >&2
  tail -n 30 "$log_file" >&2 || true
  return 1
}

wait_for_url "http://127.0.0.1:$API_PORT/docs" "FastAPI" "$API_PID" "$API_LOG"
wait_for_url "http://127.0.0.1:$CLIENT_PORT/" "React client" "$CLIENT_PID" "$CLIENT_LOG"

DEMO_URL="http://127.0.0.1:$CLIENT_PORT/"
echo
echo "Project $PROJECT_ID is ready: $DEMO_URL"
echo "API documentation: http://127.0.0.1:$API_PORT/docs"
echo "Press Ctrl-C once to stop both processes."

if [[ "${DEMO_NO_OPEN:-0}" != "1" ]] && command -v open >/dev/null 2>&1; then
  open "$DEMO_URL" >/dev/null 2>&1 || true
fi

while kill -0 "$API_PID" >/dev/null 2>&1 && kill -0 "$CLIENT_PID" >/dev/null 2>&1; do
  sleep 1
done

echo "A demo process stopped unexpectedly." >&2
echo "FastAPI log:" >&2
tail -n 30 "$API_LOG" >&2 || true
echo "Client log:" >&2
tail -n 30 "$CLIENT_LOG" >&2 || true
exit 1
