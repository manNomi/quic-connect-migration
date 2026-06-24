#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RUN_ID="${RUN_ID:-local-h3-midflight-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
UPLOAD_ADDR="${UPLOAD_ADDR:-127.0.0.1:4244}"
DOWNLOAD_ADDR="${DOWNLOAD_ADDR:-127.0.0.1:4245}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
MIGRATION_AT_BYTES="${MIGRATION_AT_BYTES:-0}"
CHUNK_BYTES="${CHUNK_BYTES:-16384}"
CHUNK_DELAY="${CHUNK_DELAY:-2ms}"
TIMEOUT="${TIMEOUT:-45s}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5s}"

mkdir -p "$ARTIFACT_DIR"

SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

run_case() {
  local mode="$1"
  local addr="$2"
  local case_dir="$ARTIFACT_DIR/$mode"

  mkdir -p "$case_dir/logs" "$case_dir/results" "$case_dir/qlog" "$case_dir/keylog"

  go run ./cmd/h3server \
    -addr "$addr" \
    -log "$case_dir/logs/h3server.jsonl" \
    -result "$case_dir/results/h3server.json" \
    -keylog "$case_dir/keylog/h3server.keys" \
    -qlog-dir "$case_dir/qlog" \
    -expected-requests 1 \
    -completion-grace 500ms \
    -timeout "$TIMEOUT" \
    >"$case_dir/logs/h3server.stdout.log" 2>&1 &
  SERVER_PID=$!

  sleep 1

  go run ./cmd/h3client \
    -server "$addr" \
    -payload-bytes "$PAYLOAD_BYTES" \
    -probe-timeout "$PROBE_TIMEOUT" \
    -timeout "$TIMEOUT" \
    -mode "$mode" \
    -migration-at-bytes "$MIGRATION_AT_BYTES" \
    -chunk-bytes "$CHUNK_BYTES" \
    -chunk-delay "$CHUNK_DELAY" \
    -log "$case_dir/logs/h3client.jsonl" \
    -result "$case_dir/results/h3client.json" \
    -keylog "$case_dir/keylog/h3client.keys" \
    -qlog-dir "$case_dir/qlog" \
    >"$case_dir/logs/h3client.stdout.log" 2>&1

  wait "$SERVER_PID"
  SERVER_PID=""

  if command -v rg >/dev/null 2>&1; then
    rg -n "path_challenge|path_response|http3:frame|chosen_alpn" "$case_dir/qlog" >"$case_dir/results/qlog-path-validation.txt" || true
  else
    grep -R -n -E "path_challenge|path_response|http3:frame|chosen_alpn" "$case_dir/qlog" >"$case_dir/results/qlog-path-validation.txt" || true
  fi
}

run_case "midflight-upload" "$UPLOAD_ADDR"
run_case "midflight-download" "$DOWNLOAD_ADDR"

python3 - "$ARTIFACT_DIR" <<'PY'
import json
import pathlib
import sys

base = pathlib.Path(sys.argv[1])
summary = {
    "status": "PASS",
    "artifact_dir": str(base),
    "cases": [],
}

for mode in ("midflight-upload", "midflight-download"):
    case_dir = base / mode
    client = json.load(open(case_dir / "results" / "h3client.json"))
    server = json.load(open(case_dir / "results" / "h3server.json"))
    if not client.get("ok"):
        raise SystemExit(f"{mode} client failed: {client.get('error')}")
    if not server.get("ok"):
        raise SystemExit(f"{mode} server failed: {server.get('error')}")
    if client.get("mode") != mode:
        raise SystemExit(f"{mode} client mode mismatch: {client.get('mode')}")
    if not client.get("local_addr_changed_to_socket_b"):
        raise SystemExit(f"{mode} client did not switch to socket B")
    tasks = client.get("tasks", [])
    requests = server.get("requests", [])
    if len(tasks) != 1:
        raise SystemExit(f"{mode} expected 1 client task, got {len(tasks)}")
    if len(requests) != 1:
        raise SystemExit(f"{mode} expected 1 server request, got {len(requests)}")
    task = tasks[0]
    request = requests[0]
    if not task.get("migration_triggered"):
        raise SystemExit(f"{mode} did not record migration trigger")
    if not request.get("decode_successful"):
        raise SystemExit(f"{mode} server/client payload decode was not successful")
    summary["cases"].append({
        "mode": mode,
        "client_socket_a": client.get("socket_a_local_addr"),
        "client_socket_b": client.get("socket_b_local_addr"),
        "after_addr": client.get("connection_local_addr_after_after_request"),
        "migration_at_bytes": task.get("migration_at_bytes"),
        "request_bytes": task.get("request_bytes"),
        "response_bytes": task.get("response_bytes"),
        "server_workload": request.get("workload"),
    })

print(json.dumps(summary, indent=2))
PY
