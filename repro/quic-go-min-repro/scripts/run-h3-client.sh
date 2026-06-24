#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 0 ]]; then
  SERVER_ADDR="$1"
else
  SERVER_ADDR="${SERVER_ADDR:-}"
fi

if [[ -z "$SERVER_ADDR" ]]; then
  echo "usage: SERVER_ADDR=<server-host>:4243 $0" >&2
  echo "   or: $0 <server-host>:4243" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

BIND_ADDR="${BIND_ADDR:-0.0.0.0:0}"
AUTHORITY="${AUTHORITY:-quic-cm-repro.local}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-65536}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5s}"
TIMEOUT="${TIMEOUT:-60s}"
POST_SEND_WAIT="${POST_SEND_WAIT:-2s}"
MODE="${MODE:-upload-download}"
MIGRATION_AT_BYTES="${MIGRATION_AT_BYTES:-0}"
CHUNK_BYTES="${CHUNK_BYTES:-16384}"
CHUNK_DELAY="${CHUNK_DELAY:-2ms}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/h3-client-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

if ! command -v go >/dev/null 2>&1 && [[ -x /usr/local/go/bin/go ]]; then
  export PATH="/usr/local/go/bin:$PATH"
fi

go run ./cmd/h3client \
  --server "$SERVER_ADDR" \
  --bind "$BIND_ADDR" \
  --authority "$AUTHORITY" \
  --payload-bytes "$PAYLOAD_BYTES" \
  --probe-timeout "$PROBE_TIMEOUT" \
  --mode "$MODE" \
  --migration-at-bytes "$MIGRATION_AT_BYTES" \
  --chunk-bytes "$CHUNK_BYTES" \
  --chunk-delay "$CHUNK_DELAY" \
  --log "$ARTIFACT_DIR/logs/client.jsonl" \
  --result "$ARTIFACT_DIR/results/client.json" \
  --qlog-dir "$ARTIFACT_DIR/qlog" \
  --keylog "$ARTIFACT_DIR/keylog/client.keys" \
  --post-send-wait "$POST_SEND_WAIT" \
  --timeout "$TIMEOUT" \
  >"$ARTIFACT_DIR/logs/client.stdout.log" 2>&1

if command -v rg >/dev/null 2>&1; then
  rg -n "path_challenge|path_response|http3:frame|chosen_alpn" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
else
  grep -R -n -E "path_challenge|path_response|http3:frame|chosen_alpn" "$ARTIFACT_DIR/qlog" >"$ARTIFACT_DIR/results/qlog-path-validation.txt" || true
fi

printf 'h3 client artifacts: %s\n' "$ARTIFACT_DIR"
