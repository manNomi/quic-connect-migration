#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-return-path-drop-controls-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
BASE_PORT="${BASE_PORT:-6700}"
REBIND_AFTER="${REBIND_AFTER:-500ms}"
TIMEOUT="${TIMEOUT:-35s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-28}"
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
  local drop_a="$7"
  local drop_b="$8"
  local expected_status="$9"
  python3 - "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$REBIND_AFTER" "$drop_a" "$drop_b" "$expected_status" <<'PY'
import json
import sys
from pathlib import Path

artifact_dir, profile, workload, bytes_value, chunks, duration_ms, rebind_after, drop_a, drop_b, expected_status = sys.argv[1:]
path = Path(artifact_dir) / "results" / "return-path-drop-spec.json"
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
            "drop_a_server_after_switch": drop_a == "1",
            "drop_b_server_after_switch": drop_b == "1",
            "expected_status": expected_status,
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
  local drop_a="$6"
  local drop_b="$7"
  local expected_status="$8"

  local proxy_port=$((BASE_PORT + (run_index * 2)))
  local server_port=$((proxy_port + 1))
  local artifact_dir="$ARTIFACT_ROOT/$profile"
  local run_id="$MATRIX_ID-$profile"
  run_specs+=("$workload:$artifact_dir")
  rm -rf "$artifact_dir"
  write_spec "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$drop_a" "$drop_b" "$expected_status"

  RUN_ID="$run_id" \
    ARTIFACT_DIR="$artifact_dir" \
    PROXY_ADDR="127.0.0.1:${proxy_port}" \
    SERVER_ADDR="127.0.0.1:${server_port}" \
    WORKLOAD="$workload" \
    REBIND_AFTER="$REBIND_AFTER" \
    DROP_A_SERVER_AFTER_SWITCH="$drop_a" \
    DROP_B_SERVER_AFTER_SWITCH="$drop_b" \
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

run_case "downlink-1m-drop-b-only" "downlink" 1048576 16 8000 0 1 PASS
run_case "upload-1m-drop-b-only" "upload" 1048576 16 8000 0 1 PASS
run_case "downlink-1m-drop-a-and-b" "downlink" 1048576 16 8000 1 1 FAIL
run_case "upload-1m-drop-a-and-b" "upload" 1048576 16 8000 1 1 FAIL

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_return_path_drop_controls.py" "${run_specs[@]}" \
  --output "$ARTIFACT_ROOT/results/return-path-drop-controls-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/return-path-drop-controls-summary.csv"
