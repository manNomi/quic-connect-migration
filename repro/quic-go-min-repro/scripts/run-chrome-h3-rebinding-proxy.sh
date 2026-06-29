#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-chrome-h3-rebinding-proxy-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PROXY_ADDR="${PROXY_ADDR:-127.0.0.1:4443}"
SERVER_ADDR="${SERVER_ADDR:-127.0.0.1:4444}"
REBIND_AFTER="${REBIND_AFTER:-3s}"
DROP_A_SERVER_AFTER_SWITCH="${DROP_A_SERVER_AFTER_SWITCH:-0}"
DROP_B_SERVER_AFTER_SWITCH="${DROP_B_SERVER_AFTER_SWITCH:-0}"
DROP_A_SERVER_AFTER_SWITCH_FOR="${DROP_A_SERVER_AFTER_SWITCH_FOR:-0}"
DROP_B_SERVER_AFTER_SWITCH_FOR="${DROP_B_SERVER_AFTER_SWITCH_FOR:-0}"
ALLOW_CLASSIFIER_FAIL="${ALLOW_CLASSIFIER_FAIL:-0}"
WORKLOAD="${WORKLOAD:-downlink}"
TIMEOUT="${TIMEOUT:-45s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-35}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-22}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Everything}"
NODE_BIN="${NODE_BIN:-node}"

case "$WORKLOAD" in
  downlink)
    DOWNLINK_DURATION_MS="${DOWNLINK_DURATION_MS:-15000}"
    DOWNLINK_CHUNKS="${DOWNLINK_CHUNKS:-15}"
    DOWNLINK_BYTES="${DOWNLINK_BYTES:-65536}"
    DOWNLINK_HEARTBEAT="${DOWNLINK_HEARTBEAT:-false}"
    DOWNLINK_HEARTBEAT_DELAY_MS="${DOWNLINK_HEARTBEAT_DELAY_MS:-$((DOWNLINK_DURATION_MS / 2))}"
    DOWNLINK_RETRY_ATTEMPTS="${DOWNLINK_RETRY_ATTEMPTS:-0}"
    DOWNLINK_RETRY_DELAY_MS="${DOWNLINK_RETRY_DELAY_MS:-500}"
    DOWNLINK_COMPLETION_GRACE_MS="${DOWNLINK_COMPLETION_GRACE_MS:-$((DOWNLINK_DURATION_MS * (DOWNLINK_RETRY_ATTEMPTS + 1) + DOWNLINK_RETRY_DELAY_MS * DOWNLINK_RETRY_ATTEMPTS + 1000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${DOWNLINK_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-downlink?duration_ms=${DOWNLINK_DURATION_MS}&chunks=${DOWNLINK_CHUNKS}&bytes=${DOWNLINK_BYTES}&heartbeat=${DOWNLINK_HEARTBEAT}&heartbeat_delay_ms=${DOWNLINK_HEARTBEAT_DELAY_MS}&retry_attempts=${DOWNLINK_RETRY_ATTEMPTS}&retry_delay_ms=${DOWNLINK_RETRY_DELAY_MS}&label=chrome-rebinding-downlink}"
    if [[ "$DOWNLINK_HEARTBEAT" == "true" || "$DOWNLINK_HEARTBEAT" == "1" ]]; then
      EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-3}"
    else
      EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
    fi
    ;;
  poll)
    POLL_COUNT="${POLL_COUNT:-5}"
    POLL_INTERVAL_MS="${POLL_INTERVAL_MS:-500}"
    POLL_COMPLETION_GRACE_MS="${POLL_COMPLETION_GRACE_MS:-$((POLL_COUNT * POLL_INTERVAL_MS + 2000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${POLL_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-poll?count=${POLL_COUNT}&interval_ms=${POLL_INTERVAL_MS}&label=chrome-rebinding-poll}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((POLL_COUNT + 1))}"
    ;;
  media)
    MEDIA_SEGMENTS="${MEDIA_SEGMENTS:-8}"
    MEDIA_INTERVAL_MS="${MEDIA_INTERVAL_MS:-250}"
    MEDIA_SEGMENT_BYTES="${MEDIA_SEGMENT_BYTES:-32768}"
    MEDIA_SEGMENT_DURATION_MS="${MEDIA_SEGMENT_DURATION_MS:-100}"
    MEDIA_SEGMENT_CHUNKS="${MEDIA_SEGMENT_CHUNKS:-2}"
    MEDIA_RETRY_ATTEMPTS="${MEDIA_RETRY_ATTEMPTS:-0}"
    MEDIA_RETRY_DELAY_MS="${MEDIA_RETRY_DELAY_MS:-500}"
    MEDIA_COMPLETION_GRACE_MS="${MEDIA_COMPLETION_GRACE_MS:-$((MEDIA_SEGMENTS * (MEDIA_INTERVAL_MS + MEDIA_SEGMENT_DURATION_MS) * (MEDIA_RETRY_ATTEMPTS + 1) + MEDIA_RETRY_DELAY_MS * MEDIA_RETRY_ATTEMPTS + 2000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${MEDIA_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-media-segments?count=${MEDIA_SEGMENTS}&interval_ms=${MEDIA_INTERVAL_MS}&bytes=${MEDIA_SEGMENT_BYTES}&segment_duration_ms=${MEDIA_SEGMENT_DURATION_MS}&segment_chunks=${MEDIA_SEGMENT_CHUNKS}&retry_attempts=${MEDIA_RETRY_ATTEMPTS}&retry_delay_ms=${MEDIA_RETRY_DELAY_MS}&label=chrome-rebinding-media}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((MEDIA_SEGMENTS + 1))}"
    ;;
  buffered-media)
    BUFFERED_MEDIA_SEGMENTS="${BUFFERED_MEDIA_SEGMENTS:-8}"
    BUFFERED_MEDIA_SEGMENT_BYTES="${BUFFERED_MEDIA_SEGMENT_BYTES:-32768}"
    BUFFERED_MEDIA_SEGMENT_DURATION_MS="${BUFFERED_MEDIA_SEGMENT_DURATION_MS:-100}"
    BUFFERED_MEDIA_SEGMENT_CHUNKS="${BUFFERED_MEDIA_SEGMENT_CHUNKS:-2}"
    BUFFERED_MEDIA_PLAYBACK_INTERVAL_MS="${BUFFERED_MEDIA_PLAYBACK_INTERVAL_MS:-1000}"
    BUFFERED_MEDIA_STARTUP_BUFFER_SEGMENTS="${BUFFERED_MEDIA_STARTUP_BUFFER_SEGMENTS:-2}"
    BUFFERED_MEDIA_MAX_BUFFER_SEGMENTS="${BUFFERED_MEDIA_MAX_BUFFER_SEGMENTS:-4}"
    BUFFERED_MEDIA_RETRY_ATTEMPTS="${BUFFERED_MEDIA_RETRY_ATTEMPTS:-0}"
    BUFFERED_MEDIA_RETRY_DELAY_MS="${BUFFERED_MEDIA_RETRY_DELAY_MS:-500}"
    BUFFERED_MEDIA_COMPLETION_GRACE_MS="${BUFFERED_MEDIA_COMPLETION_GRACE_MS:-$((BUFFERED_MEDIA_SEGMENTS * BUFFERED_MEDIA_PLAYBACK_INTERVAL_MS + BUFFERED_MEDIA_SEGMENTS * BUFFERED_MEDIA_SEGMENT_DURATION_MS * (BUFFERED_MEDIA_RETRY_ATTEMPTS + 1) + BUFFERED_MEDIA_RETRY_DELAY_MS * BUFFERED_MEDIA_RETRY_ATTEMPTS + 3000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${BUFFERED_MEDIA_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-buffered-media?count=${BUFFERED_MEDIA_SEGMENTS}&bytes=${BUFFERED_MEDIA_SEGMENT_BYTES}&segment_duration_ms=${BUFFERED_MEDIA_SEGMENT_DURATION_MS}&segment_chunks=${BUFFERED_MEDIA_SEGMENT_CHUNKS}&playback_interval_ms=${BUFFERED_MEDIA_PLAYBACK_INTERVAL_MS}&startup_buffer_segments=${BUFFERED_MEDIA_STARTUP_BUFFER_SEGMENTS}&max_buffer_segments=${BUFFERED_MEDIA_MAX_BUFFER_SEGMENTS}&retry_attempts=${BUFFERED_MEDIA_RETRY_ATTEMPTS}&retry_delay_ms=${BUFFERED_MEDIA_RETRY_DELAY_MS}&label=chrome-rebinding-buffered-media}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((BUFFERED_MEDIA_SEGMENTS + 1))}"
    ;;
  range)
    RANGE_TOTAL_BYTES="${RANGE_TOTAL_BYTES:-1048576}"
    RANGE_CHUNK_BYTES="${RANGE_CHUNK_BYTES:-131072}"
    RANGE_CHUNK_COUNT="${RANGE_CHUNK_COUNT:-$(((RANGE_TOTAL_BYTES + RANGE_CHUNK_BYTES - 1) / RANGE_CHUNK_BYTES))}"
    RANGE_CHUNK_DURATION_MS="${RANGE_CHUNK_DURATION_MS:-250}"
    RANGE_RESPONSE_CHUNKS="${RANGE_RESPONSE_CHUNKS:-2}"
    RANGE_RETRY_ATTEMPTS="${RANGE_RETRY_ATTEMPTS:-0}"
    RANGE_RETRY_DELAY_MS="${RANGE_RETRY_DELAY_MS:-500}"
    RANGE_COMPLETION_GRACE_MS="${RANGE_COMPLETION_GRACE_MS:-$((RANGE_CHUNK_COUNT * (RANGE_CHUNK_DURATION_MS + RANGE_RETRY_DELAY_MS * RANGE_RETRY_ATTEMPTS) + 3000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${RANGE_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-range-download?bytes=${RANGE_TOTAL_BYTES}&range_bytes=${RANGE_CHUNK_BYTES}&range_duration_ms=${RANGE_CHUNK_DURATION_MS}&range_chunks=${RANGE_RESPONSE_CHUNKS}&retry_attempts=${RANGE_RETRY_ATTEMPTS}&retry_delay_ms=${RANGE_RETRY_DELAY_MS}&label=chrome-rebinding-range}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-$((RANGE_CHUNK_COUNT + 1))}"
    ;;
  upload)
    UPLOAD_DURATION_MS="${UPLOAD_DURATION_MS:-6000}"
    UPLOAD_CHUNKS="${UPLOAD_CHUNKS:-6}"
    UPLOAD_BYTES="${UPLOAD_BYTES:-65536}"
    UPLOAD_RETRY_ATTEMPTS="${UPLOAD_RETRY_ATTEMPTS:-0}"
    UPLOAD_RETRY_DELAY_MS="${UPLOAD_RETRY_DELAY_MS:-500}"
    UPLOAD_COMPLETION_GRACE_MS="${UPLOAD_COMPLETION_GRACE_MS:-$((UPLOAD_DURATION_MS * (UPLOAD_RETRY_ATTEMPTS + 1) + UPLOAD_RETRY_DELAY_MS * UPLOAD_RETRY_ATTEMPTS + 1000))}"
    COMPLETION_GRACE="${COMPLETION_GRACE:-${UPLOAD_COMPLETION_GRACE_MS}ms}"
    REQUEST_PATH="${REQUEST_PATH:-/browser-upload?duration_ms=${UPLOAD_DURATION_MS}&chunks=${UPLOAD_CHUNKS}&bytes=${UPLOAD_BYTES}&retry_attempts=${UPLOAD_RETRY_ATTEMPTS}&retry_delay_ms=${UPLOAD_RETRY_DELAY_MS}&label=chrome-rebinding-upload}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
    ;;
  *)
    echo "unsupported WORKLOAD=$WORKLOAD" >&2
    exit 2
    ;;
esac

mkdir -p "$ARTIFACT_DIR/bin" "$ARTIFACT_DIR/chrome" "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome binary not found or not executable: $CHROME_BIN" >&2
  exit 2
fi

CERT_FILE="$ARTIFACT_DIR/certs/server.pem"
KEY_FILE="$ARTIFACT_DIR/certs/server-key.pem"
SPKI_FILE="$ARTIFACT_DIR/certs/server.spki"

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
LISTEN_ADDR="$SERVER_ADDR" \
TIMEOUT="$TIMEOUT" \
COMPLETION_GRACE="${COMPLETION_GRACE:-500ms}" \
./scripts/run-h3-server.sh >"$ARTIFACT_DIR/logs/server-wrapper.log" 2>&1 &
SERVER_PID=$!

go build -o "$ARTIFACT_DIR/bin/udprebindproxy" ./cmd/udprebindproxy

PROXY_ARGS=(
  --listen "$PROXY_ADDR"
  --server "$SERVER_ADDR"
  --switch-after "$REBIND_AFTER"
  --timeout "$TIMEOUT"
  --log "$ARTIFACT_DIR/logs/rebinding-proxy.jsonl"
  --result "$ARTIFACT_DIR/results/rebinding-proxy.json"
)
if [[ "$DROP_A_SERVER_AFTER_SWITCH" == "1" || "$DROP_A_SERVER_AFTER_SWITCH" == "true" ]]; then
  PROXY_ARGS+=(--drop-a-server-after-switch)
fi
if [[ "$DROP_B_SERVER_AFTER_SWITCH" == "1" || "$DROP_B_SERVER_AFTER_SWITCH" == "true" ]]; then
  PROXY_ARGS+=(--drop-b-server-after-switch)
fi
if [[ "$DROP_A_SERVER_AFTER_SWITCH_FOR" != "0" ]]; then
  PROXY_ARGS+=(--drop-a-server-after-switch-for "$DROP_A_SERVER_AFTER_SWITCH_FOR")
fi
if [[ "$DROP_B_SERVER_AFTER_SWITCH_FOR" != "0" ]]; then
  PROXY_ARGS+=(--drop-b-server-after-switch-for "$DROP_B_SERVER_AFTER_SWITCH_FOR")
fi

"$ARTIFACT_DIR/bin/udprebindproxy" "${PROXY_ARGS[@]}" \
  >"$ARTIFACT_DIR/logs/rebinding-proxy.stdout.log" 2>&1 &
PROXY_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if kill -0 "$PROXY_PID" >/dev/null 2>&1; then
    kill "$PROXY_PID" >/dev/null 2>&1 || true
    wait "$PROXY_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 2

"$NODE_BIN" "$PROJECT_ROOT/tools/run_chrome_cdp_navigation.js" \
  --chrome-bin "$CHROME_BIN" \
  --artifact-dir "$ARTIFACT_DIR" \
  --url "https://${PROXY_ADDR}${REQUEST_PATH}" \
  --origin-to-force-quic-on "$PROXY_ADDR" \
  --spki-hash "$SPKI_HASH" \
  --netlog-name "netlog.json" \
  --dump-name "dump-dom.txt" \
  --net-log-capture-mode "$CHROME_NET_LOG_CAPTURE_MODE" \
  --timeout-seconds "$CHROME_TIMEOUT_SECONDS" \
  --hold-seconds "$CHROME_HOLD_SECONDS" || CHROME_EXIT=$?
CHROME_EXIT="${CHROME_EXIT:-0}"

SERVER_EXIT=0
wait "$SERVER_PID" || SERVER_EXIT=$?

PROXY_EXIT=0
if kill -0 "$PROXY_PID" >/dev/null 2>&1; then
  kill "$PROXY_PID" >/dev/null 2>&1 || true
fi
wait "$PROXY_PID" || PROXY_EXIT=$?
trap - EXIT

CLASSIFIER_EXIT=0
python3 "$PROJECT_ROOT/tools/classify_chrome_h3_artifacts.py" "$ARTIFACT_DIR" \
  --addr "$PROXY_ADDR" \
  --expected-requests "$EXPECTED_REQUESTS" \
  --workload "rebinding-proxy-${WORKLOAD}" \
  --chrome-exit "$CHROME_EXIT" \
  --server-exit "$SERVER_EXIT" \
  --output "$ARTIFACT_DIR/results/chrome-summary.json" || CLASSIFIER_EXIT=$?

python3 - "$ARTIFACT_DIR/results/chrome-summary.json" "$ARTIFACT_DIR/results/rebinding-proxy.json" "$PROXY_EXIT" "$CLASSIFIER_EXIT" <<'PY'
import json
import sys
summary_path, proxy_path, proxy_exit, classifier_exit = sys.argv[1:]
summary = json.load(open(summary_path, encoding="utf-8"))
proxy = json.load(open(proxy_path, encoding="utf-8")) if __import__("pathlib").Path(proxy_path).exists() else {}
summary["rebinding_proxy"] = {
    "proxy_exit": int(proxy_exit),
    "switched": proxy.get("switched"),
    "upstream_a_addr": proxy.get("upstream_a_addr"),
    "upstream_b_addr": proxy.get("upstream_b_addr"),
    "client_packets": proxy.get("client_packets"),
    "server_packets_a": proxy.get("server_packets_a"),
    "server_packets_b": proxy.get("server_packets_b"),
    "drop_a_server_after_switch": proxy.get("drop_a_server_after_switch"),
    "drop_b_server_after_switch": proxy.get("drop_b_server_after_switch"),
    "drop_a_server_after_switch_for_ms": proxy.get("drop_a_server_after_switch_for_ms"),
    "drop_b_server_after_switch_for_ms": proxy.get("drop_b_server_after_switch_for_ms"),
    "dropped_server_packets_a": proxy.get("dropped_server_packets_a"),
    "dropped_server_packets_b": proxy.get("dropped_server_packets_b"),
    "dropped_server_bytes_a": proxy.get("dropped_server_bytes_a"),
    "dropped_server_bytes_b": proxy.get("dropped_server_bytes_b"),
}
summary["classifier_exit"] = int(classifier_exit)
with open(summary_path, "w", encoding="utf-8") as fp:
    json.dump(summary, fp, indent=2)
    fp.write("\n")
print(json.dumps(summary, indent=2))
PY

if [[ "$CLASSIFIER_EXIT" != "0" && "$ALLOW_CLASSIFIER_FAIL" != "1" && "$ALLOW_CLASSIFIER_FAIL" != "true" ]]; then
  exit "$CLASSIFIER_EXIT"
fi
