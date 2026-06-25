#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

ADB_BIN="${ADB_BIN:-adb}"
ANDROID_SERIAL="${ANDROID_SERIAL:-}"
ANDROID_CHROME_PACKAGE="${ANDROID_CHROME_PACKAGE:-com.android.chrome}"
RUN_ID="${RUN_ID:-android-chrome-controlled-public-h3-network-change-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:?set PUBLIC_ORIGIN_URL, e.g. https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=android-handover-slow}"
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-$ARTIFACT_DIR}"
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}"
REQUIRE_CONTROLLED_PUBLIC_BASELINE="${REQUIRE_CONTROLLED_PUBLIC_BASELINE:-1}"
NETWORK_CHANGE_CMD="${ANDROID_NETWORK_CHANGE_CMD:-${NETWORK_CHANGE_CMD:-}}"
NETWORK_CHANGE_AFTER_SECONDS="${NETWORK_CHANGE_AFTER_SECONDS:-3}"
REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}"
ANDROID_CHROME_WAIT_SECONDS="${ANDROID_CHROME_WAIT_SECONDS:-18}"
ANDROID_FORCE_STOP="${ANDROID_FORCE_STOP:-1}"
SERVER_RESULT_WAIT_SECONDS="${SERVER_RESULT_WAIT_SECONDS:-15}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-7}"

"$SCRIPT_DIR/ensure-min-disk-free.sh" "$MIN_ARTIFACT_FREE_GIB" "$REPRO_DIR"

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/android"

if ! command -v "$ADB_BIN" >/dev/null 2>&1; then
  echo "adb not found: $ADB_BIN" >&2
  exit 2
fi

if [[ -z "$NETWORK_CHANGE_CMD" ]]; then
  echo "set ANDROID_NETWORK_CHANGE_CMD or NETWORK_CHANGE_CMD to the Android active path/interface change command" >&2
  exit 2
fi

ADB_ARGS=("$ADB_BIN")
if [[ -n "$ANDROID_SERIAL" ]]; then
  ADB_ARGS+=("-s" "$ANDROID_SERIAL")
fi

capture_android_snapshot() {
  local label="$1"
  "${ADB_ARGS[@]}" shell dumpsys connectivity >"$ARTIFACT_DIR/android/connectivity-${label}.txt" 2>"$ARTIFACT_DIR/logs/connectivity-${label}.stderr.log" || true
  "${ADB_ARGS[@]}" shell ip route >"$ARTIFACT_DIR/android/ip-route-${label}.txt" 2>"$ARTIFACT_DIR/logs/ip-route-${label}.stderr.log" || true
  "${ADB_ARGS[@]}" shell ip addr show >"$ARTIFACT_DIR/android/ip-addr-${label}.txt" 2>"$ARTIFACT_DIR/logs/ip-addr-${label}.stderr.log" || true
}

if [[ "$REQUIRE_CONTROLLED_PUBLIC_BASELINE" == "1" ]]; then
  if [[ -z "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" || ! -f "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" ]]; then
    echo "set CONTROLLED_PUBLIC_BASELINE_SUMMARY to a prior controlled-public baseline summary with status starting PASS" >&2
    exit 2
  fi
  python3 - "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1], encoding="utf-8"))
status = str(summary.get("status") or "")
if not status.startswith("PASS"):
    raise SystemExit(f"controlled public baseline gate did not pass: {summary.get('status')} / {summary.get('classification')}")
PY
fi

READINESS_ARGS=(--url "$PUBLIC_ORIGIN_URL" --format json)
if [[ "$REQUIRE_H3_ALT_SVC" == "1" ]]; then
  READINESS_ARGS+=(--require-h3-alt-svc)
fi
python3 "$PROJECT_ROOT/tools/check_public_origin_readiness.py" "${READINESS_ARGS[@]}" \
  >"$ARTIFACT_DIR/results/public-origin-readiness.json"

capture_android_snapshot "before"

(
  sleep "$NETWORK_CHANGE_AFTER_SECONDS"
  STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  capture_android_snapshot "command-before"
  EXIT_CODE=0
  bash -lc "$NETWORK_CHANGE_CMD" || EXIT_CODE=$?
  COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  capture_android_snapshot "command-after"
  python3 "$PROJECT_ROOT/tools/compare_android_path_snapshots.py" \
    --before-route "$ARTIFACT_DIR/android/ip-route-command-before.txt" \
    --after-route "$ARTIFACT_DIR/android/ip-route-command-after.txt" \
    --before-addr "$ARTIFACT_DIR/android/ip-addr-command-before.txt" \
    --after-addr "$ARTIFACT_DIR/android/ip-addr-command-after.txt" \
    --before-connectivity "$ARTIFACT_DIR/android/connectivity-command-before.txt" \
    --after-connectivity "$ARTIFACT_DIR/android/connectivity-command-after.txt" \
    --output "$ARTIFACT_DIR/results/client-path-change-summary.json" || true
  python3 - "$ARTIFACT_DIR/results/network-change.json" "$EXIT_CODE" "$STARTED_AT" "$COMPLETED_AT" <<'PY'
import json
import sys

output, exit_code, started_at, completed_at = sys.argv[1:]
data = {
    "command_present": True,
    "exit": int(exit_code),
    "started_at": started_at,
    "completed_at": completed_at,
}
with open(output, "w", encoding="utf-8") as fp:
    json.dump(data, fp, indent=2)
    fp.write("\n")
PY
  exit "$EXIT_CODE"
) >"$ARTIFACT_DIR/logs/network-change.log" 2>&1 &
NETWORK_CHANGE_PID=$!

ANDROID_EXIT=0
ANDROID_ARGS=(
  --adb-bin "$ADB_BIN"
  --url "$PUBLIC_ORIGIN_URL"
  --package "$ANDROID_CHROME_PACKAGE"
  --wait-seconds "$ANDROID_CHROME_WAIT_SECONDS"
  --output "$ARTIFACT_DIR/results/android-chrome-navigation.json"
)
if [[ -n "$ANDROID_SERIAL" ]]; then
  ANDROID_ARGS+=(--serial "$ANDROID_SERIAL")
fi
if [[ "$ANDROID_FORCE_STOP" == "1" ]]; then
  ANDROID_ARGS+=(--force-stop)
fi
python3 "$PROJECT_ROOT/tools/run_android_chrome_navigation.py" "${ANDROID_ARGS[@]}" || ANDROID_EXIT=$?

NETWORK_CHANGE_EXIT=0
wait "$NETWORK_CHANGE_PID" || NETWORK_CHANGE_EXIT=$?
if [[ ! -f "$ARTIFACT_DIR/results/network-change.json" ]]; then
  python3 - "$ARTIFACT_DIR/results/network-change.json" "$NETWORK_CHANGE_EXIT" <<'PY'
import json
import sys

output, exit_code = sys.argv[1:]
with open(output, "w", encoding="utf-8") as fp:
    json.dump({"command_present": True, "exit": int(exit_code)}, fp, indent=2)
    fp.write("\n")
PY
fi

capture_android_snapshot "final"

if [[ -f "$ARTIFACT_DIR/android/ip-route-command-before.txt" && -f "$ARTIFACT_DIR/android/ip-route-command-after.txt" && ! -f "$ARTIFACT_DIR/results/client-path-change-summary.json" ]]; then
  python3 "$PROJECT_ROOT/tools/compare_android_path_snapshots.py" \
    --before-route "$ARTIFACT_DIR/android/ip-route-command-before.txt" \
    --after-route "$ARTIFACT_DIR/android/ip-route-command-after.txt" \
    --before-addr "$ARTIFACT_DIR/android/ip-addr-command-before.txt" \
    --after-addr "$ARTIFACT_DIR/android/ip-addr-command-after.txt" \
    --before-connectivity "$ARTIFACT_DIR/android/connectivity-command-before.txt" \
    --after-connectivity "$ARTIFACT_DIR/android/connectivity-command-after.txt" \
    --output "$ARTIFACT_DIR/results/client-path-change-summary.json" || true
fi

for _ in $(seq 1 "$SERVER_RESULT_WAIT_SECONDS"); do
  if [[ -f "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR/results/server.json" ]]; then
    break
  fi
  sleep 1
done

CLASSIFIER_ARGS=(
  "$ARTIFACT_DIR"
  --server-artifact-dir "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR"
  --url "$PUBLIC_ORIGIN_URL"
  --browser-kind android-chrome
  --browser-exit "$ANDROID_EXIT"
  --allow-missing-browser-netlog
  --output "$ARTIFACT_DIR/results/android-chrome-controlled-public-h3-network-change-summary.json"
)
if [[ -n "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" ]]; then
  CLASSIFIER_ARGS+=(--expected-requests "$CONTROLLED_PUBLIC_EXPECTED_REQUESTS")
fi
python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_network_change.py" "${CLASSIFIER_ARGS[@]}"
