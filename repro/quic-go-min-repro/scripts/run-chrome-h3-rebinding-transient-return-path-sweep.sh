#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-transient-return-path-sweep-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
BASE_PORT="${BASE_PORT:-6800}"
REBIND_AFTER="${REBIND_AFTER:-500ms}"
TIMEOUT="${TIMEOUT:-38s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-32}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-14}"

mkdir -p "$ARTIFACT_ROOT/results"

run_index=0
run_specs=()

write_spec() {
  local artifact_dir="$1"
  local profile="$2"
  local workload="$3"
  local bytes="$4"
  local chunks="$5"
  local duration_ms="$6"
  local drop_window="$7"
  local drop_window_ms="$8"
  python3 - "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$REBIND_AFTER" "$drop_window" "$drop_window_ms" <<'PY'
import json
import sys
from pathlib import Path

artifact_dir, profile, workload, bytes_value, chunks, duration_ms, rebind_after, drop_window, drop_window_ms = sys.argv[1:]
path = Path(artifact_dir) / "results" / "transient-return-path-spec.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    json.dumps(
        {
            "profile": profile,
            "workload": workload,
            "bytes": int(bytes_value),
            "chunks": int(chunks),
            "duration_ms": int(duration_ms),
            "rebind_after": rebind_after,
            "drop_a_server_after_switch": True,
            "drop_b_server_after_switch": True,
            "drop_window": drop_window,
            "drop_window_ms": int(drop_window_ms),
            "expected_status": "MEASURE",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY
}

run_case() {
  local profile="$1"
  local workload="$2"
  local bytes="$3"
  local chunks="$4"
  local duration_ms="$5"
  local drop_window="$6"
  local drop_window_ms="$7"

  local proxy_port=$((BASE_PORT + (run_index * 2)))
  local server_port=$((proxy_port + 1))
  local artifact_dir="$ARTIFACT_ROOT/$profile"
  local run_id="$MATRIX_ID-$profile"
  run_specs+=("$workload:$artifact_dir")
  rm -rf "$artifact_dir"
  write_spec "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$drop_window" "$drop_window_ms"

  RUN_ID="$run_id" \
    ARTIFACT_DIR="$artifact_dir" \
    PROXY_ADDR="127.0.0.1:${proxy_port}" \
    SERVER_ADDR="127.0.0.1:${server_port}" \
    WORKLOAD="$workload" \
    REBIND_AFTER="$REBIND_AFTER" \
    DROP_A_SERVER_AFTER_SWITCH=1 \
    DROP_B_SERVER_AFTER_SWITCH=1 \
    DROP_A_SERVER_AFTER_SWITCH_FOR="$drop_window" \
    DROP_B_SERVER_AFTER_SWITCH_FOR="$drop_window" \
    ALLOW_CLASSIFIER_FAIL=1 \
    TIMEOUT="$TIMEOUT" \
    CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
    CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
    EXPECTED_REQUESTS=2 \
    DOWNLINK_HEARTBEAT=false \
    DOWNLINK_BYTES="$bytes" \
    DOWNLINK_CHUNKS="$chunks" \
    DOWNLINK_DURATION_MS="$duration_ms" \
    UPLOAD_BYTES="$bytes" \
    UPLOAD_CHUNKS="$chunks" \
    UPLOAD_DURATION_MS="$duration_ms" \
    ./scripts/run-chrome-h3-rebinding-proxy.sh

  run_index=$((run_index + 1))
}

run_case "downlink-1m-drop-ab-250ms" "downlink" 1048576 16 8000 250ms 250
run_case "upload-1m-drop-ab-250ms" "upload" 1048576 16 8000 250ms 250
run_case "downlink-1m-drop-ab-1500ms" "downlink" 1048576 16 8000 1500ms 1500
run_case "upload-1m-drop-ab-1500ms" "upload" 1048576 16 8000 1500ms 1500
run_case "downlink-1m-drop-ab-3000ms" "downlink" 1048576 16 8000 3000ms 3000
run_case "upload-1m-drop-ab-3000ms" "upload" 1048576 16 8000 3000ms 3000
run_case "downlink-1m-drop-ab-6000ms" "downlink" 1048576 16 8000 6000ms 6000
run_case "upload-1m-drop-ab-6000ms" "upload" 1048576 16 8000 6000ms 6000
run_case "downlink-1m-drop-ab-9000ms" "downlink" 1048576 16 8000 9000ms 9000
run_case "upload-1m-drop-ab-9000ms" "upload" 1048576 16 8000 9000ms 9000

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_transient_return_path_sweep.py" "${run_specs[@]}" \
  --output "$ARTIFACT_ROOT/results/transient-return-path-sweep-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/transient-return-path-sweep-summary.csv"
