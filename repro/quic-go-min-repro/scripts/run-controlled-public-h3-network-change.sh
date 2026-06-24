#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-controlled-public-h3-network-change-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:?set PUBLIC_ORIGIN_URL, e.g. https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow}"
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-$ARTIFACT_DIR}"
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}"
REQUIRE_CONTROLLED_PUBLIC_BASELINE="${REQUIRE_CONTROLLED_PUBLIC_BASELINE:-1}"
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set NETWORK_CHANGE_CMD to the active path/interface change command}"
NETWORK_CHANGE_AFTER_SECONDS="${NETWORK_CHANGE_AFTER_SECONDS:-2}"
REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-30}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Everything}"
CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-0}"
CHROME_RUNNER="${CHROME_RUNNER:-dump-dom}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-15}"
NODE_BIN="${NODE_BIN:-node}"
SERVER_RESULT_WAIT_SECONDS="${SERVER_RESULT_WAIT_SECONDS:-15}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-5}"

"$SCRIPT_DIR/ensure-min-disk-free.sh" "$MIN_ARTIFACT_FREE_GIB" "$REPRO_DIR"

mkdir -p "$ARTIFACT_DIR/chrome" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome binary not found or not executable: $CHROME_BIN" >&2
  exit 2
fi

if [[ "$REQUIRE_CONTROLLED_PUBLIC_BASELINE" == "1" ]]; then
  if [[ -z "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" || ! -f "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" ]]; then
    echo "set CONTROLLED_PUBLIC_BASELINE_SUMMARY to a prior controlled-public-h3-baseline-summary.json with status=PASS" >&2
    exit 2
  fi
  python3 - "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1], encoding="utf-8"))
if summary.get("status") != "PASS":
    raise SystemExit(f"controlled public baseline gate did not PASS: {summary.get('status')} / {summary.get('classification')}")
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

CHROME_EXIT=0
if [[ "$CHROME_RUNNER" == "cdp" ]]; then
  "$NODE_BIN" "$PROJECT_ROOT/tools/run_chrome_cdp_navigation.js" \
    --chrome-bin "$CHROME_BIN" \
    --artifact-dir "$ARTIFACT_DIR" \
    --url "$PUBLIC_ORIGIN_URL" \
    --netlog-name "network-change-netlog.json" \
    --dump-name "network-change-dump-dom.txt" \
    --net-log-capture-mode "$CHROME_NET_LOG_CAPTURE_MODE" \
    --timeout-seconds "$CHROME_TIMEOUT_SECONDS" \
    --hold-seconds "$CHROME_HOLD_SECONDS" || CHROME_EXIT=$?
elif [[ "$CHROME_RUNNER" == "dump-dom" ]]; then
  python3 - "$CHROME_BIN" "$ARTIFACT_DIR" "$PUBLIC_ORIGIN_URL" "$CHROME_TIMEOUT_SECONDS" "$CHROME_NET_LOG_CAPTURE_MODE" "$CHROME_VIRTUAL_TIME_BUDGET_MS" <<'PY' || CHROME_EXIT=$?
import os
import pathlib
import shlex
import subprocess
import sys

chrome_bin, artifact_dir, url, timeout_s, net_log_capture_mode, virtual_time_budget_ms = sys.argv[1:]
artifact = pathlib.Path(artifact_dir)
cmd = [
    chrome_bin,
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-extensions",
    "--disable-domain-reliability",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--metrics-recording-only",
    "--password-store=basic",
    "--safebrowsing-disable-auto-update",
    "--disable-features=AutofillServerCommunication,CertificateTransparencyComponentUpdater,InterestFeedContentSuggestions,MediaRouter,OptimizationGuideModelDownloading,OptimizationHints,OptimizationTargetPrediction,SafeBrowsingEnhancedProtection",
    "--enable-quic",
    f"--user-data-dir={artifact / 'chrome' / 'profile'}",
    f"--log-net-log={artifact / 'chrome' / 'network-change-netlog.json'}",
    f"--net-log-capture-mode={net_log_capture_mode}",
    "--dump-dom",
    url,
]
if int(virtual_time_budget_ms) > 0:
    cmd.insert(-2, f"--virtual-time-budget={virtual_time_budget_ms}")
extra_args = os.environ.get("CHROME_EXTRA_ARGS", "")
if extra_args:
    cmd[1:1] = shlex.split(extra_args)
with (artifact / "chrome" / "network-change-dump-dom.txt").open("wb") as out, (artifact / "chrome" / "network-change-dump-dom.txt.stderr.log").open("wb") as err:
    try:
        subprocess.run(cmd, stdout=out, stderr=err, timeout=int(timeout_s), check=True)
    except subprocess.TimeoutExpired:
        raise SystemExit(124)
PY
else
  echo "unsupported CHROME_RUNNER=$CHROME_RUNNER" >&2
  CHROME_EXIT=2
fi

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
  --chrome-exit "$CHROME_EXIT"
  --output "$ARTIFACT_DIR/results/controlled-public-h3-network-change-summary.json"
)
if [[ -n "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" ]]; then
  CLASSIFIER_ARGS+=(--expected-requests "$CONTROLLED_PUBLIC_EXPECTED_REQUESTS")
fi
python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_network_change.py" "${CLASSIFIER_ARGS[@]}"
