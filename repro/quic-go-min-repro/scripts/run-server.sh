#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

LISTEN_ADDR="${LISTEN_ADDR:-0.0.0.0:4242}"
TIMEOUT="${TIMEOUT:-120s}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/server-$(date -u +%Y%m%dT%H%M%SZ)}"
SERVER_ID="${SERVER_ID:-}"

mkdir -p "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

if ! command -v go >/dev/null 2>&1 && [[ -x /usr/local/go/bin/go ]]; then
  export PATH="/usr/local/go/bin:$PATH"
fi

exec go run ./cmd/server \
  --addr "$LISTEN_ADDR" \
  --log "$ARTIFACT_DIR/logs/server.jsonl" \
  --result "$ARTIFACT_DIR/results/server.json" \
  --qlog-dir "$ARTIFACT_DIR/qlog" \
  --keylog "$ARTIFACT_DIR/keylog/server.keys" \
  --server-id "$SERVER_ID" \
  --timeout "$TIMEOUT"
