#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command python3
require_command networksetup
require_command route
require_command ifconfig

CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
if [[ -f "$CONFIG_FILE" ]]; then
  load_env_if_present "$CONFIG_FILE"
fi

REPRO_DIR="$PROJECT_ROOT/repro/quic-go-min-repro"
TRIAL_ID="${TRIAL_ID:-controlled-public-chrome-downlink-iphone-usb-precutover-nochange-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$REPRO_DIR/artifacts/$TRIAL_ID}"
BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-${PUBLIC_ORIGIN_URL:-}}"
WORKLOAD_URL="${PUBLIC_ORIGIN_PRECUTOVER_URL:-${PUBLIC_ORIGIN_NOCHANGE_URL:-${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-}}}"
EXPECTED_REQUESTS="${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-5}"
WIFI_DEVICE="${WIFI_DEVICE:-en0}"
IPHONE_USB_DEVICE="${IPHONE_USB_DEVICE:-en8}"
PRECUTOVER_WAIT_SECONDS="${PRECUTOVER_WAIT_SECONDS:-12}"
PUBLIC_IP_PROBE_URL="${PUBLIC_IP_PROBE_URL:-https://ifconfig.me/ip}"
CHROME_RUNNER="${CHROME_RUNNER:-cdp}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-20}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-45}"
CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-0}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Default}"
RUN_CONTROLLED_PUBLIC_CLASSIFIER="${RUN_CONTROLLED_PUBLIC_CLASSIFIER:-0}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-7}"
RUNNER="${RUNNER:-$REPRO_DIR/scripts/run-controlled-public-h3-browser-baseline.sh}"
DRY_RUN="${DRY_RUN:-0}"

if [[ -z "$BOOTSTRAP_URL" ]]; then
  echo "PUBLIC_ORIGIN_URL or PUBLIC_ORIGIN_BOOTSTRAP_URL is required" >&2
  exit 2
fi
if [[ -z "$WORKLOAD_URL" ]]; then
  echo "PUBLIC_ORIGIN_PRECUTOVER_URL, PUBLIC_ORIGIN_NOCHANGE_URL, or PUBLIC_ORIGIN_NETWORK_CHANGE_URL is required" >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

restore_wifi() {
  networksetup -setairportpower "$WIFI_DEVICE" on >/dev/null 2>&1 || true
  python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
    --url "$WORKLOAD_URL" \
    --public-ip-url "$PUBLIC_IP_PROBE_URL" \
    --timeout 5 \
    --output "$ARTIFACT_DIR/results/client-path-after-restore.json" >/dev/null 2>&1 || true
}

print_kv "trial_id" "$TRIAL_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
print_kv "bootstrap_url" "$BOOTSTRAP_URL"
print_kv "workload_url" "$WORKLOAD_URL"
print_kv "wifi_device" "$WIFI_DEVICE"
print_kv "iphone_usb_device" "$IPHONE_USB_DEVICE"
print_kv "expected_requests" "$EXPECTED_REQUESTS"
print_kv "chrome_runner" "$CHROME_RUNNER"
print_kv "dry_run" "$DRY_RUN"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "chrome_iphone_usb_precutover_control=dry-run"
  exit 0
fi

trap restore_wifi EXIT

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$WORKLOAD_URL" \
  --public-ip-url "$PUBLIC_IP_PROBE_URL" \
  --timeout 5 \
  --output "$ARTIFACT_DIR/results/client-path-before.json"

networksetup -setairportpower "$WIFI_DEVICE" off
for elapsed in $(seq 1 "$PRECUTOVER_WAIT_SECONDS"); do
  sleep 1
  iface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2}' || true)"
  usb_ipv4="$(ifconfig "$IPHONE_USB_DEVICE" 2>/dev/null | awk '/inet /{print $2}' | head -n 1 || true)"
  print_kv "precutover_wait_${elapsed}s" "iface=${iface:-none} ${IPHONE_USB_DEVICE}_ipv4=${usb_ipv4:-none}"
  if [[ "$iface" == "$IPHONE_USB_DEVICE" && -n "$usb_ipv4" ]]; then
    break
  fi
  if [[ "$elapsed" == "$PRECUTOVER_WAIT_SECONDS" ]]; then
    echo "iPhone USB did not become default route within ${PRECUTOVER_WAIT_SECONDS}s" >&2
    exit 42
  fi
done

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$WORKLOAD_URL" \
  --public-ip-url "$PUBLIC_IP_PROBE_URL" \
  --timeout 5 \
  --output "$ARTIFACT_DIR/results/client-path-precutover.json"

env \
  RUN_ID="$TRIAL_ID" \
  ARTIFACT_DIR="$ARTIFACT_DIR" \
  PUBLIC_ORIGIN_URL="$BOOTSTRAP_URL" \
  PUBLIC_ORIGIN_BOOTSTRAP_URL="$BOOTSTRAP_URL" \
  SECOND_URL="$WORKLOAD_URL" \
  CONTROLLED_PUBLIC_EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
  RUN_CONTROLLED_PUBLIC_CLASSIFIER="$RUN_CONTROLLED_PUBLIC_CLASSIFIER" \
  REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}" \
  MIN_ARTIFACT_FREE_GIB="$MIN_ARTIFACT_FREE_GIB" \
  CHROME_BIN="${CHROME_BIN:-}" \
  CHROME_RUNNER="$CHROME_RUNNER" \
  CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
  CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
  CHROME_VIRTUAL_TIME_BUDGET_MS="$CHROME_VIRTUAL_TIME_BUDGET_MS" \
  CHROME_NET_LOG_CAPTURE_MODE="$CHROME_NET_LOG_CAPTURE_MODE" \
  "$RUNNER"

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$WORKLOAD_URL" \
  --public-ip-url "$PUBLIC_IP_PROBE_URL" \
  --timeout 5 \
  --output "$ARTIFACT_DIR/results/client-path-before-restore.json"

echo "chrome_iphone_usb_precutover_control=complete"
