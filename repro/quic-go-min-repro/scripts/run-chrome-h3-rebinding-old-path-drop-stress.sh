#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-old-path-drop-stress-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
BASE_PORT="${BASE_PORT:-6200}"
REBIND_AFTER="${REBIND_AFTER:-500ms}"
TIMEOUT="${TIMEOUT:-35s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-30}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-14}"

mkdir -p "$ARTIFACT_ROOT/results"

run_index=0
run_specs=()

write_spec() {
  local artifact_dir="$1"
  local profile="$2"
  local workload="$3"
  local heartbeat="$4"
  local bytes="$5"
  local chunks="$6"
  local duration_ms="$7"
  python3 - "$artifact_dir" "$profile" "$workload" "$heartbeat" "$bytes" "$chunks" "$duration_ms" "$REBIND_AFTER" <<'PY'
import json
import sys
from pathlib import Path

artifact_dir, profile, workload, heartbeat, bytes_value, chunks, duration_ms, rebind_after = sys.argv[1:]
path = Path(artifact_dir) / "results" / "stress-spec.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    json.dumps(
        {
            "profile": profile,
            "workload": workload,
            "heartbeat": heartbeat,
            "bytes": int(bytes_value),
            "chunks": int(chunks),
            "duration_ms": int(duration_ms),
            "rebind_after": rebind_after,
            "drop_a_server_after_switch": True,
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
  local heartbeat="$3"
  local bytes="$4"
  local chunks="$5"
  local duration_ms="$6"

  local proxy_port=$((BASE_PORT + (run_index * 2)))
  local server_port=$((proxy_port + 1))
  local artifact_dir="$ARTIFACT_ROOT/$profile"
  local run_id="$MATRIX_ID-$profile"
  run_specs+=("$workload:$artifact_dir")
  write_spec "$artifact_dir" "$profile" "$workload" "$heartbeat" "$bytes" "$chunks" "$duration_ms"

  local expected_requests=2
  if [[ "$workload" == "downlink" && "$heartbeat" == "true" ]]; then
    expected_requests=3
  fi

  RUN_ID="$run_id" \
    ARTIFACT_DIR="$artifact_dir" \
    PROXY_ADDR="127.0.0.1:${proxy_port}" \
    SERVER_ADDR="127.0.0.1:${server_port}" \
    WORKLOAD="$workload" \
    REBIND_AFTER="$REBIND_AFTER" \
    DROP_A_SERVER_AFTER_SWITCH=1 \
    TIMEOUT="$TIMEOUT" \
    CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
    CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
    EXPECTED_REQUESTS="$expected_requests" \
    DOWNLINK_HEARTBEAT="$heartbeat" \
    DOWNLINK_HEARTBEAT_DELAY_MS="$((duration_ms / 2))" \
    DOWNLINK_BYTES="$bytes" \
    DOWNLINK_CHUNKS="$chunks" \
    DOWNLINK_DURATION_MS="$duration_ms" \
    UPLOAD_BYTES="$bytes" \
    UPLOAD_CHUNKS="$chunks" \
    UPLOAD_DURATION_MS="$duration_ms" \
    ./scripts/run-chrome-h3-rebinding-proxy.sh

  run_index=$((run_index + 1))
}

run_case "downlink-1m-noheartbeat" "downlink" "false" 1048576 16 8000
run_case "downlink-1m-heartbeat" "downlink" "true" 1048576 16 8000
run_case "downlink-4m-noheartbeat" "downlink" "false" 4194304 32 12000
run_case "upload-1m" "upload" "n/a" 1048576 16 8000
run_case "upload-4m" "upload" "n/a" 4194304 32 12000

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_stress_matrix.py" "${run_specs[@]}" \
  --output "$ARTIFACT_ROOT/results/stress-matrix-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/stress-matrix-summary.csv"
