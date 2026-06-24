#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-chrome-h3-local-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
ADDR="${ADDR:-127.0.0.1:4443}"
LISTEN_ADDR="${LISTEN_ADDR:-$ADDR}"
ORIGIN_ADDR="${ORIGIN_ADDR:-$ADDR}"
WORKLOAD="${WORKLOAD:-single}"
case "$WORKLOAD" in
  single)
    REQUEST_PATH="${REQUEST_PATH:-/download?bytes=128&label=chrome-baseline}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-1}"
    ;;
  sequence)
    SEQUENCE_RESOURCES="${SEQUENCE_RESOURCES:-2}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-sequence?resources=${SEQUENCE_RESOURCES}&bytes=128&label=chrome-sequence}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((SEQUENCE_RESOURCES + 1))}"
    ;;
  poll)
    POLL_COUNT="${POLL_COUNT:-5}"
    POLL_INTERVAL_MS="${POLL_INTERVAL_MS:-500}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-poll?count=${POLL_COUNT}&interval_ms=${POLL_INTERVAL_MS}&label=chrome-poll}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((POLL_COUNT + 1))}"
    ;;
  slow)
    SLOW_DURATION_MS="${SLOW_DURATION_MS:-6000}"
    SLOW_CHUNKS="${SLOW_CHUNKS:-6}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-slow?duration_ms=${SLOW_DURATION_MS}&chunks=${SLOW_CHUNKS}&label=chrome-slow}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
    ;;
  downlink)
    DOWNLINK_DURATION_MS="${DOWNLINK_DURATION_MS:-15000}"
    DOWNLINK_CHUNKS="${DOWNLINK_CHUNKS:-15}"
    DOWNLINK_BYTES="${DOWNLINK_BYTES:-65536}"
    DOWNLINK_HEARTBEAT="${DOWNLINK_HEARTBEAT:-false}"
    DOWNLINK_HEARTBEAT_DELAY_MS="${DOWNLINK_HEARTBEAT_DELAY_MS:-$((DOWNLINK_DURATION_MS / 2))}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-downlink?duration_ms=${DOWNLINK_DURATION_MS}&chunks=${DOWNLINK_CHUNKS}&bytes=${DOWNLINK_BYTES}&heartbeat=${DOWNLINK_HEARTBEAT}&heartbeat_delay_ms=${DOWNLINK_HEARTBEAT_DELAY_MS}&label=chrome-downlink}"
    if [[ "$DOWNLINK_HEARTBEAT" == "true" || "$DOWNLINK_HEARTBEAT" == "1" ]]; then
      EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-3}"
    else
      EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
    fi
    ;;
  *)
    echo "unsupported WORKLOAD=$WORKLOAD" >&2
    exit 2
    ;;
esac
TIMEOUT="${TIMEOUT:-60s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-20}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Everything}"
CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-5000}"

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

NETWORK_CHANGE_PID=""
if [[ -n "${NETWORK_CHANGE_CMD:-}" ]]; then
  (
    sleep "${NETWORK_CHANGE_AFTER_SECONDS:-2}"
    bash -lc "$NETWORK_CHANGE_CMD"
  ) >"$ARTIFACT_DIR/logs/network-change.log" 2>&1 &
  NETWORK_CHANGE_PID=$!
fi

CHROME_EXIT=0
python3 - "$CHROME_BIN" "$ARTIFACT_DIR" "$ORIGIN_ADDR" "$REQUEST_PATH" "$SPKI_HASH" "$CHROME_TIMEOUT_SECONDS" "$CHROME_NET_LOG_CAPTURE_MODE" "$CHROME_VIRTUAL_TIME_BUDGET_MS" <<'PY' || CHROME_EXIT=$?
import pathlib
import subprocess
import sys

chrome_bin, artifact_dir, addr, request_path, spki_hash, timeout_s, net_log_capture_mode, virtual_time_budget_ms = sys.argv[1:]
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
    "--enable-quic",
    f"--origin-to-force-quic-on={addr}",
    f"--ignore-certificate-errors-spki-list={spki_hash}",
    f"--user-data-dir={artifact / 'chrome' / 'profile'}",
    f"--log-net-log={artifact / 'chrome' / 'netlog.json'}",
    f"--net-log-capture-mode={net_log_capture_mode}",
    "--dump-dom",
    url,
]
if int(virtual_time_budget_ms) > 0:
    cmd.insert(-2, f"--virtual-time-budget={virtual_time_budget_ms}")
with (artifact / "chrome" / "dump-dom.txt").open("wb") as out, (artifact / "chrome" / "chrome.stderr.log").open("wb") as err:
    try:
        subprocess.run(cmd, stdout=out, stderr=err, timeout=int(timeout_s), check=True)
    except subprocess.TimeoutExpired:
        raise SystemExit(124)
PY

NETWORK_CHANGE_EXIT=0
if [[ -n "$NETWORK_CHANGE_PID" ]]; then
  wait "$NETWORK_CHANGE_PID" || NETWORK_CHANGE_EXIT=$?
  printf '{"exit":%s}\n' "$NETWORK_CHANGE_EXIT" >"$ARTIFACT_DIR/results/network-change.json"
fi

SERVER_EXIT=0
wait "$SERVER_PID" || SERVER_EXIT=$?
trap - EXIT

python3 "$PROJECT_ROOT/tools/classify_chrome_h3_artifacts.py" "$ARTIFACT_DIR" \
  --addr "$ORIGIN_ADDR" \
  --expected-requests "$EXPECTED_REQUESTS" \
  --workload "$WORKLOAD" \
  --chrome-exit "$CHROME_EXIT" \
  --server-exit "$SERVER_EXIT" \
  --output "$ARTIFACT_DIR/results/chrome-summary.json"
