#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-chrome-h3-alt-svc-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
ADDR="${ADDR:-127.0.0.1:4443}"
LISTEN_ADDR="${LISTEN_ADDR:-$ADDR}"
TCP_ADDR="${TCP_ADDR:-$LISTEN_ADDR}"
EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
TIMEOUT="${TIMEOUT:-60s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-20}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Everything}"
CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-5000}"
BOOTSTRAP_PATH="${BOOTSTRAP_PATH:-/download?bytes=128&label=alt-svc-bootstrap}"
H3_PATH="${H3_PATH:-/download?bytes=128&label=alt-svc-h3}"
ALT_SVC="${ALT_SVC:-h3=\":${ADDR##*:}\"; ma=60}"

mkdir -p "$ARTIFACT_DIR/chrome" "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

CERT_FILE="$ARTIFACT_DIR/certs/server.pem"
KEY_FILE="$ARTIFACT_DIR/certs/server-key.pem"
SPKI_FILE="$ARTIFACT_DIR/certs/server.spki"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome binary not found or not executable: $CHROME_BIN" >&2
  exit 2
fi

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -days 1 \
  -subj "/CN=quic-cm-repro.local" \
  -addext "subjectAltName=DNS:localhost,DNS:quic-cm-repro.local,IP:127.0.0.1,IP:::1" \
  >/dev/null 2>&1

SPKI_HASH="$(
  openssl x509 -pubkey -noout -in "$CERT_FILE" |
    openssl pkey -pubin -outform der |
    openssl dgst -sha256 -binary |
    base64
)"
printf '%s\n' "$SPKI_HASH" >"$SPKI_FILE"

QUIC_CM_CERT_FILE="$CERT_FILE" \
QUIC_CM_KEY_FILE="$KEY_FILE" \
EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
ARTIFACT_DIR="$ARTIFACT_DIR" \
LISTEN_ADDR="$LISTEN_ADDR" \
TCP_ADDR="$TCP_ADDR" \
ALT_SVC="$ALT_SVC" \
TIMEOUT="$TIMEOUT" \
./scripts/run-h3-server.sh >"$ARTIFACT_DIR/logs/server-wrapper.log" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 2

run_chrome() {
  local path="$1"
  local netlog="$2"
  local dump="$3"
  python3 - "$CHROME_BIN" "$ARTIFACT_DIR" "$ADDR" "$path" "$SPKI_HASH" "$CHROME_TIMEOUT_SECONDS" "$CHROME_NET_LOG_CAPTURE_MODE" "$CHROME_VIRTUAL_TIME_BUDGET_MS" "$netlog" "$dump" <<'PY'
import os
import pathlib
import shlex
import subprocess
import sys

chrome_bin, artifact_dir, addr, request_path, spki_hash, timeout_s, net_log_capture_mode, virtual_time_budget_ms, netlog_name, dump_name = sys.argv[1:]
artifact = pathlib.Path(artifact_dir)
url = f"https://{addr}{request_path}"
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
    f"--ignore-certificate-errors-spki-list={spki_hash}",
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
run_chrome "$BOOTSTRAP_PATH" "bootstrap-netlog.json" "bootstrap-dump-dom.txt" || BOOTSTRAP_EXIT=$?

sleep 1

H3_EXIT=0
run_chrome "$H3_PATH" "h3-netlog.json" "h3-dump-dom.txt" || H3_EXIT=$?

SERVER_EXIT=0
wait "$SERVER_PID" || SERVER_EXIT=$?
trap - EXIT

python3 "$PROJECT_ROOT/tools/classify_chrome_alt_svc_artifacts.py" "$ARTIFACT_DIR" \
  --addr "$ADDR" \
  --expected-requests "$EXPECTED_REQUESTS" \
  --bootstrap-exit "$BOOTSTRAP_EXIT" \
  --h3-exit "$H3_EXIT" \
  --server-exit "$SERVER_EXIT" \
  --output "$ARTIFACT_DIR/results/chrome-alt-svc-summary.json"
