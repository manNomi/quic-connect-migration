#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-chrome-public-h3-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
TARGET_URL="${TARGET_URL:-https://cloudflare-quic.com/}"
SECOND_URL="${SECOND_URL:-$TARGET_URL}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-20}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Default}"
CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-5000}"

mkdir -p "$ARTIFACT_DIR/chrome" "$ARTIFACT_DIR/results"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome binary not found or not executable: $CHROME_BIN" >&2
  exit 2
fi

run_chrome() {
  local url="$1"
  local netlog="$2"
  local dump="$3"
  python3 - "$CHROME_BIN" "$ARTIFACT_DIR" "$url" "$CHROME_TIMEOUT_SECONDS" "$CHROME_NET_LOG_CAPTURE_MODE" "$CHROME_VIRTUAL_TIME_BUDGET_MS" "$netlog" "$dump" <<'PY'
import os
import pathlib
import shlex
import subprocess
import sys

chrome_bin, artifact_dir, url, timeout_s, net_log_capture_mode, virtual_time_budget_ms, netlog_name, dump_name = sys.argv[1:]
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
    f"--log-net-log={artifact / 'chrome' / netlog_name}",
    f"--net-log-capture-mode={net_log_capture_mode}",
    "--dump-dom",
    url,
]
if int(virtual_time_budget_ms) > 0:
    cmd.insert(-2, f"--virtual-time-budget={virtual_time_budget_ms}")
extra_args = os.environ.get("CHROME_EXTRA_ARGS", "")
if extra_args:
    cmd[1:1] = shlex.split(extra_args)
with (artifact / "chrome" / dump_name).open("wb") as out, (artifact / "chrome" / f"{dump_name}.stderr.log").open("wb") as err:
    try:
        subprocess.run(cmd, stdout=out, stderr=err, timeout=int(timeout_s), check=True)
    except subprocess.TimeoutExpired:
        raise SystemExit(124)
PY
}

BOOTSTRAP_EXIT=0
run_chrome "$TARGET_URL" "bootstrap-netlog.json" "bootstrap-dump-dom.txt" || BOOTSTRAP_EXIT=$?

sleep 1

SECOND_EXIT=0
run_chrome "$SECOND_URL" "second-netlog.json" "second-dump-dom.txt" || SECOND_EXIT=$?

python3 "$PROJECT_ROOT/tools/classify_chrome_public_h3_artifacts.py" "$ARTIFACT_DIR" \
  --url "$SECOND_URL" \
  --bootstrap-exit "$BOOTSTRAP_EXIT" \
  --second-exit "$SECOND_EXIT" \
  --output "$ARTIFACT_DIR/results/chrome-public-h3-summary.json"
