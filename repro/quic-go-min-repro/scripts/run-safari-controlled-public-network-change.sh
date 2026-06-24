#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

RUN_ID="${RUN_ID:-safari-controlled-public-h3-network-change-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:?set PUBLIC_ORIGIN_URL, e.g. https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=safari-handover-slow}"
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-$ARTIFACT_DIR}"
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}"
REQUIRE_CONTROLLED_PUBLIC_BASELINE="${REQUIRE_CONTROLLED_PUBLIC_BASELINE:-1}"
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set NETWORK_CHANGE_CMD to the active path/interface change command}"
NETWORK_CHANGE_AFTER_SECONDS="${NETWORK_CHANGE_AFTER_SECONDS:-3}"
REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}"
SAFARI_PORT="${SAFARI_PORT:-4444}"
SAFARI_WAIT_SECONDS="${SAFARI_WAIT_SECONDS:-18}"
SAFARI_DRIVER_START_TIMEOUT="${SAFARI_DRIVER_START_TIMEOUT:-10}"
SAFARI_COMMAND_TIMEOUT="${SAFARI_COMMAND_TIMEOUT:-30}"
SAFARI_PAGE_LOAD_TIMEOUT_MS="${SAFARI_PAGE_LOAD_TIMEOUT_MS:-30000}"
SAFARI_SCRIPT_TIMEOUT_MS="${SAFARI_SCRIPT_TIMEOUT_MS:-30000}"
SERVER_RESULT_WAIT_SECONDS="${SERVER_RESULT_WAIT_SECONDS:-15}"

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

if ! command -v safaridriver >/dev/null 2>&1; then
  echo "safaridriver not found" >&2
  exit 2
fi

if [[ "$REQUIRE_CONTROLLED_PUBLIC_BASELINE" == "1" ]]; then
  if [[ -z "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" || ! -f "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" ]]; then
    echo "set CONTROLLED_PUBLIC_BASELINE_SUMMARY to a prior Safari/controlled-public baseline summary with status starting PASS" >&2
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

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --output "$ARTIFACT_DIR/results/client-path-before.json" || true

(
  sleep "$NETWORK_CHANGE_AFTER_SECONDS"
  STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
    --url "$PUBLIC_ORIGIN_URL" \
    --output "$ARTIFACT_DIR/results/client-path-command-before.json" || true
  EXIT_CODE=0
  bash -lc "$NETWORK_CHANGE_CMD" || EXIT_CODE=$?
  COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
    --url "$PUBLIC_ORIGIN_URL" \
    --output "$ARTIFACT_DIR/results/client-path-command-after.json" || true
  python3 "$PROJECT_ROOT/tools/compare_network_path_snapshots.py" \
    "$ARTIFACT_DIR/results/client-path-command-before.json" \
    "$ARTIFACT_DIR/results/client-path-command-after.json" \
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

SAFARI_EXIT=0
python3 "$PROJECT_ROOT/tools/run_safari_webdriver_navigation.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --port "$SAFARI_PORT" \
  --wait-seconds "$SAFARI_WAIT_SECONDS" \
  --driver-start-timeout "$SAFARI_DRIVER_START_TIMEOUT" \
  --command-timeout "$SAFARI_COMMAND_TIMEOUT" \
  --page-load-timeout-ms "$SAFARI_PAGE_LOAD_TIMEOUT_MS" \
  --script-timeout-ms "$SAFARI_SCRIPT_TIMEOUT_MS" \
  --safaridriver-log "$ARTIFACT_DIR/logs/safaridriver.log" \
  --output "$ARTIFACT_DIR/results/safari-navigation.json" || SAFARI_EXIT=$?

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

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --output "$ARTIFACT_DIR/results/client-path-final.json" || true

if [[ -f "$ARTIFACT_DIR/results/client-path-command-before.json" && -f "$ARTIFACT_DIR/results/client-path-command-after.json" && ! -f "$ARTIFACT_DIR/results/client-path-change-summary.json" ]]; then
  python3 "$PROJECT_ROOT/tools/compare_network_path_snapshots.py" \
    "$ARTIFACT_DIR/results/client-path-command-before.json" \
    "$ARTIFACT_DIR/results/client-path-command-after.json" \
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
  --browser-kind safari
  --browser-exit "$SAFARI_EXIT"
  --allow-missing-browser-netlog
  --output "$ARTIFACT_DIR/results/safari-controlled-public-h3-network-change-summary.json"
)
if [[ -n "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" ]]; then
  CLASSIFIER_ARGS+=(--expected-requests "$CONTROLLED_PUBLIC_EXPECTED_REQUESTS")
fi
python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_network_change.py" "${CLASSIFIER_ARGS[@]}"
