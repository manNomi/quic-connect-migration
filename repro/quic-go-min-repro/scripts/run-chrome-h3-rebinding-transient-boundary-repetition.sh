#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-chrome-h3-rebinding-transient-boundary-repetition-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
BASE_PORT="${BASE_PORT:-7100}"
REBIND_AFTER="${REBIND_AFTER:-500ms}"
TIMEOUT="${TIMEOUT:-42s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-36}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-18}"
REPETITIONS="${REPETITIONS:-3}"
DROP_WINDOWS_MS="${DROP_WINDOWS_MS:-4000 4500 5000}"
WORKLOADS="${WORKLOADS:-downlink upload}"
EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
DOWNLINK_RETRY_ATTEMPTS="${DOWNLINK_RETRY_ATTEMPTS:-0}"
DOWNLINK_RETRY_DELAY_MS="${DOWNLINK_RETRY_DELAY_MS:-500}"
UPLOAD_RETRY_ATTEMPTS="${UPLOAD_RETRY_ATTEMPTS:-0}"
UPLOAD_RETRY_DELAY_MS="${UPLOAD_RETRY_DELAY_MS:-500}"
POLL_COUNT="${POLL_COUNT:-5}"
POLL_INTERVAL_MS="${POLL_INTERVAL_MS:-500}"

mkdir -p "$ARTIFACT_ROOT/results"

run_index=0
run_specs=()
read -r -a drop_windows_ms <<<"$DROP_WINDOWS_MS"
read -r -a workloads <<<"$WORKLOADS"

write_spec() {
  local artifact_dir="$1"
  local profile="$2"
  local workload="$3"
  local bytes="$4"
  local chunks="$5"
  local duration_ms="$6"
  local drop_window="$7"
  local drop_window_ms="$8"
  local repetition="$9"
  python3 - "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$REBIND_AFTER" "$drop_window" "$drop_window_ms" "$repetition" "$DOWNLINK_RETRY_ATTEMPTS" "$DOWNLINK_RETRY_DELAY_MS" "$UPLOAD_RETRY_ATTEMPTS" "$UPLOAD_RETRY_DELAY_MS" "$POLL_COUNT" "$POLL_INTERVAL_MS" <<'PY'
import json
import sys
from pathlib import Path

artifact_dir, profile, workload, bytes_value, chunks, duration_ms, rebind_after, drop_window, drop_window_ms, repetition, downlink_retry_attempts, downlink_retry_delay_ms, upload_retry_attempts, upload_retry_delay_ms, poll_count, poll_interval_ms = sys.argv[1:]
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
            "repetition": int(repetition),
            "downlink_retry_attempts": int(downlink_retry_attempts),
            "downlink_retry_delay_ms": int(downlink_retry_delay_ms),
            "upload_retry_attempts": int(upload_retry_attempts),
            "upload_retry_delay_ms": int(upload_retry_delay_ms),
            "poll_count": int(poll_count),
            "poll_interval_ms": int(poll_interval_ms),
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
  local repetition="$8"

  local proxy_port=$((BASE_PORT + (run_index * 2)))
  local server_port=$((proxy_port + 1))
  local artifact_dir="$ARTIFACT_ROOT/$profile"
  local run_id="$MATRIX_ID-$profile"
  run_specs+=("$workload:$artifact_dir")
  rm -rf "$artifact_dir"
  write_spec "$artifact_dir" "$profile" "$workload" "$bytes" "$chunks" "$duration_ms" "$drop_window" "$drop_window_ms" "$repetition"

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
    EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
    DOWNLINK_HEARTBEAT=false \
    DOWNLINK_BYTES="$bytes" \
    DOWNLINK_CHUNKS="$chunks" \
    DOWNLINK_DURATION_MS="$duration_ms" \
    DOWNLINK_RETRY_ATTEMPTS="$DOWNLINK_RETRY_ATTEMPTS" \
    DOWNLINK_RETRY_DELAY_MS="$DOWNLINK_RETRY_DELAY_MS" \
    UPLOAD_BYTES="$bytes" \
    UPLOAD_CHUNKS="$chunks" \
    UPLOAD_DURATION_MS="$duration_ms" \
    UPLOAD_RETRY_ATTEMPTS="$UPLOAD_RETRY_ATTEMPTS" \
    UPLOAD_RETRY_DELAY_MS="$UPLOAD_RETRY_DELAY_MS" \
    POLL_COUNT="$POLL_COUNT" \
    POLL_INTERVAL_MS="$POLL_INTERVAL_MS" \
    ./scripts/run-chrome-h3-rebinding-proxy.sh

  run_index=$((run_index + 1))
}

for repetition in $(seq 1 "$REPETITIONS"); do
  rep_label="$(printf "rep%02d" "$repetition")"
  for drop_window_ms in "${drop_windows_ms[@]}"; do
    drop_window="${drop_window_ms}ms"
    for workload in "${workloads[@]}"; do
      case "$workload" in
        downlink | upload | poll) ;;
        *)
          echo "unsupported workload in WORKLOADS: $workload" >&2
          exit 2
          ;;
      esac
      run_case "${rep_label}-${workload}-1m-drop-ab-${drop_window}" "$workload" 1048576 16 8000 "$drop_window" "$drop_window_ms" "$repetition"
    done
  done
done

python3 "$PROJECT_ROOT/tools/summarize_chrome_rebinding_transient_return_path_sweep.py" "${run_specs[@]}" \
  --output "$ARTIFACT_ROOT/results/transient-boundary-repetition-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/transient-boundary-repetition-summary.csv"
