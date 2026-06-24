#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-upload-matrix-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
REPEAT_COUNT="${REPEAT_COUNT:-3}"
BASE_PORT="${BASE_PORT:-4900}"
REBIND_AFTER="${REBIND_AFTER:-2s}"
DROP_A_SERVER_AFTER_SWITCH="${DROP_A_SERVER_AFTER_SWITCH:-0}"
DROP_B_SERVER_AFTER_SWITCH="${DROP_B_SERVER_AFTER_SWITCH:-0}"
TIMEOUT="${TIMEOUT:-25s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-20}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-10}"
UPLOAD_DURATION_MS="${UPLOAD_DURATION_MS:-6000}"
UPLOAD_CHUNKS="${UPLOAD_CHUNKS:-6}"
UPLOAD_BYTES="${UPLOAD_BYTES:-262144}"

mkdir -p "$ARTIFACT_ROOT/results"

artifact_dirs=()
for ((rep = 1; rep <= REPEAT_COUNT; rep += 1)); do
  proxy_port=$((BASE_PORT + ((rep - 1) * 2)))
  server_port=$((proxy_port + 1))
  run_id="${MATRIX_ID}-upload-r${rep}"
  artifact_dir="${ARTIFACT_ROOT}/upload-r${rep}"
  artifact_dirs+=("$artifact_dir")

  RUN_ID="$run_id" \
    ARTIFACT_DIR="$artifact_dir" \
    PROXY_ADDR="127.0.0.1:${proxy_port}" \
    SERVER_ADDR="127.0.0.1:${server_port}" \
    WORKLOAD=upload \
    UPLOAD_DURATION_MS="$UPLOAD_DURATION_MS" \
    UPLOAD_CHUNKS="$UPLOAD_CHUNKS" \
    UPLOAD_BYTES="$UPLOAD_BYTES" \
    REBIND_AFTER="$REBIND_AFTER" \
    DROP_A_SERVER_AFTER_SWITCH="$DROP_A_SERVER_AFTER_SWITCH" \
    DROP_B_SERVER_AFTER_SWITCH="$DROP_B_SERVER_AFTER_SWITCH" \
    TIMEOUT="$TIMEOUT" \
    CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
    CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
    ./scripts/run-chrome-h3-rebinding-proxy.sh
done

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_upload_matrix.py" "${artifact_dirs[@]}" \
  --output "$ARTIFACT_ROOT/results/upload-matrix-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/upload-matrix-summary.csv"
