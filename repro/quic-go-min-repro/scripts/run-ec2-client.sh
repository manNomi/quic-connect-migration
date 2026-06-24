#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 0 ]]; then
  SERVER_ADDR="$1"
else
  SERVER_ADDR="${SERVER_ADDR:-}"
fi

if [[ -z "$SERVER_ADDR" ]]; then
  echo "usage: SERVER_ADDR=<ec2-public-ip>:4242 $0" >&2
  echo "   or: $0 <ec2-public-ip>:4242" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

BIND_ADDR="${BIND_ADDR:-0.0.0.0:0}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5s}"
TIMEOUT="${TIMEOUT:-60s}"
POST_SEND_WAIT="${POST_SEND_WAIT:-2s}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/ec2-client-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

if ! command -v go >/dev/null 2>&1 && [[ -x /usr/local/go/bin/go ]]; then
  export PATH="/usr/local/go/bin:$PATH"
fi

go run ./cmd/client \
  --server "$SERVER_ADDR" \
  --bind "$BIND_ADDR" \
  --payload-bytes "$PAYLOAD_BYTES" \
  --probe-timeout "$PROBE_TIMEOUT" \
  --log "$ARTIFACT_DIR/logs/client.jsonl" \
  --result "$ARTIFACT_DIR/results/client.json" \
  --qlog-dir "$ARTIFACT_DIR/qlog" \
  --keylog "$ARTIFACT_DIR/keylog/client.keys" \
  --post-send-wait "$POST_SEND_WAIT" \
  --timeout "$TIMEOUT" \
  >"$ARTIFACT_DIR/logs/client.stdout.log" 2>&1

if command -v rg >/dev/null 2>&1; then
  rg -n "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
else
  grep -R -n -E "path_challenge|path_response" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
fi

printf 'ec2 client artifacts: %s\n' "$ARTIFACT_DIR"
