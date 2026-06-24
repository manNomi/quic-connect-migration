#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

PORT="${PORT:-4242}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-3s}"
TIMEOUT="${TIMEOUT:-30s}"
RUN_ID="${RUN_ID:-local-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
SERVER_ID="${SERVER_ID:-}"
POST_SEND_WAIT="${POST_SEND_WAIT:-2s}"

mkdir -p "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

go test ./...

go run ./cmd/server \
  --addr "127.0.0.1:${PORT}" \
  --log "$ARTIFACT_DIR/logs/server.jsonl" \
  --result "$ARTIFACT_DIR/results/server.json" \
  --qlog-dir "$ARTIFACT_DIR/qlog" \
  --keylog "$ARTIFACT_DIR/keylog/server.keys" \
  --server-id "$SERVER_ID" \
  --timeout "$TIMEOUT" \
  >"$ARTIFACT_DIR/logs/server.stdout.log" 2>&1 &

SERVER_PID="$!"
cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 1

go run ./cmd/client \
  --server "127.0.0.1:${PORT}" \
  --bind "127.0.0.1:0" \
  --payload-bytes "$PAYLOAD_BYTES" \
  --probe-timeout "$PROBE_TIMEOUT" \
  --log "$ARTIFACT_DIR/logs/client.jsonl" \
  --result "$ARTIFACT_DIR/results/client.json" \
  --qlog-dir "$ARTIFACT_DIR/qlog" \
  --keylog "$ARTIFACT_DIR/keylog/client.keys" \
  --post-send-wait "$POST_SEND_WAIT" \
  --timeout "$TIMEOUT" \
  >"$ARTIFACT_DIR/logs/client.stdout.log" 2>&1

wait "$SERVER_PID"
trap - EXIT

if command -v rg >/dev/null 2>&1; then
  rg -n "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
else
  grep -R -n -E "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
fi

printf 'local happy-path artifacts: %s\n' "$ARTIFACT_DIR"
