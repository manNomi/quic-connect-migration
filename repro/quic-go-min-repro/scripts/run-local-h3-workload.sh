#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_ID="${RUN_ID:-local-h3-workload-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
ADDR="${ADDR:-127.0.0.1:4243}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-65536}"
TIMEOUT="${TIMEOUT:-30s}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-3s}"

mkdir -p "${ARTIFACT_DIR}/logs" "${ARTIFACT_DIR}/results" "${ARTIFACT_DIR}/qlog" "${ARTIFACT_DIR}/keylog"

SERVER_LOG="${ARTIFACT_DIR}/logs/h3server.jsonl"
CLIENT_LOG="${ARTIFACT_DIR}/logs/h3client.jsonl"
SERVER_RESULT="${ARTIFACT_DIR}/results/h3server.json"
CLIENT_RESULT="${ARTIFACT_DIR}/results/h3client.json"

go run ./cmd/h3server \
  -addr "$ADDR" \
  -log "$SERVER_LOG" \
  -result "$SERVER_RESULT" \
  -keylog "${ARTIFACT_DIR}/keylog/h3server.keys" \
  -qlog-dir "${ARTIFACT_DIR}/qlog" \
  -timeout "$TIMEOUT" \
  >"${ARTIFACT_DIR}/logs/h3server.stdout.log" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 1

go run ./cmd/h3client \
  -server "$ADDR" \
  -payload-bytes "$PAYLOAD_BYTES" \
  -probe-timeout "$PROBE_TIMEOUT" \
  -timeout "$TIMEOUT" \
  -log "$CLIENT_LOG" \
  -result "$CLIENT_RESULT" \
  -keylog "${ARTIFACT_DIR}/keylog/h3client.keys" \
  -qlog-dir "${ARTIFACT_DIR}/qlog" \
  >"${ARTIFACT_DIR}/logs/h3client.stdout.log" 2>&1

wait "$SERVER_PID"
trap - EXIT

python3 - "$CLIENT_RESULT" "$SERVER_RESULT" <<'PY'
import json
import sys
client = json.load(open(sys.argv[1]))
server = json.load(open(sys.argv[2]))
if not client.get("ok"):
    raise SystemExit(f"client failed: {client.get('error')}")
if not server.get("ok"):
    raise SystemExit(f"server failed: {server.get('error')}")
if not client.get("local_addr_changed_to_socket_b"):
    raise SystemExit("client did not switch to socket B")
if len(client.get("tasks", [])) != 2:
    raise SystemExit("client did not complete two HTTP/3 tasks")
if len(server.get("requests", [])) != 2:
    raise SystemExit("server did not observe two HTTP/3 requests")
print(json.dumps({
    "status": "PASS",
    "artifact_dir": sys.argv[1].rsplit("/results/", 1)[0],
    "client_socket_a": client.get("socket_a_local_addr"),
    "client_socket_b": client.get("socket_b_local_addr"),
    "after_addr": client.get("connection_local_addr_after_after_request"),
    "tasks": [task.get("label") for task in client.get("tasks", [])],
}, indent=2))
PY
