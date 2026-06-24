#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-matrix-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
REPEAT_COUNT="${REPEAT_COUNT:-3}"
BASE_PORT="${BASE_PORT:-4700}"
REBIND_AFTER="${REBIND_AFTER:-2s}"
DROP_A_SERVER_AFTER_SWITCH="${DROP_A_SERVER_AFTER_SWITCH:-0}"
DROP_B_SERVER_AFTER_SWITCH="${DROP_B_SERVER_AFTER_SWITCH:-0}"
TIMEOUT="${TIMEOUT:-25s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-20}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-10}"
DOWNLINK_DURATION_MS="${DOWNLINK_DURATION_MS:-6000}"
DOWNLINK_CHUNKS="${DOWNLINK_CHUNKS:-6}"
DOWNLINK_BYTES="${DOWNLINK_BYTES:-32768}"
DOWNLINK_HEARTBEAT_DELAY_MS="${DOWNLINK_HEARTBEAT_DELAY_MS:-3000}"

mkdir -p "$ARTIFACT_ROOT/results"

run_index=0
artifact_dirs=()
for heartbeat in false true; do
  if [[ "$heartbeat" == "true" ]]; then
    mode="heartbeat"
  else
    mode="noheartbeat"
  fi
  for ((rep = 1; rep <= REPEAT_COUNT; rep += 1)); do
    proxy_port=$((BASE_PORT + (run_index * 2)))
    server_port=$((proxy_port + 1))
    run_id="${MATRIX_ID}-${mode}-r${rep}"
    artifact_dir="${ARTIFACT_ROOT}/${mode}-r${rep}"
    artifact_dirs+=("$artifact_dir")

    RUN_ID="$run_id" \
      ARTIFACT_DIR="$artifact_dir" \
      PROXY_ADDR="127.0.0.1:${proxy_port}" \
      SERVER_ADDR="127.0.0.1:${server_port}" \
      WORKLOAD=downlink \
      DOWNLINK_DURATION_MS="$DOWNLINK_DURATION_MS" \
      DOWNLINK_CHUNKS="$DOWNLINK_CHUNKS" \
      DOWNLINK_BYTES="$DOWNLINK_BYTES" \
      DOWNLINK_HEARTBEAT="$heartbeat" \
      DOWNLINK_HEARTBEAT_DELAY_MS="$DOWNLINK_HEARTBEAT_DELAY_MS" \
      REBIND_AFTER="$REBIND_AFTER" \
      DROP_A_SERVER_AFTER_SWITCH="$DROP_A_SERVER_AFTER_SWITCH" \
      DROP_B_SERVER_AFTER_SWITCH="$DROP_B_SERVER_AFTER_SWITCH" \
      TIMEOUT="$TIMEOUT" \
      CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
      CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
      ./scripts/run-chrome-h3-rebinding-proxy.sh

    run_index=$((run_index + 1))
  done
done

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_proxy_matrix.py" "${artifact_dirs[@]}" \
  --output "$ARTIFACT_ROOT/results/matrix-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/matrix-summary.csv"
