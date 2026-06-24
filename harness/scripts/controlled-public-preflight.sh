#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
CONFIG_PRESENT=0
if [[ -f "$CONFIG_FILE" ]]; then
  CONFIG_PRESENT=1
  load_env_if_present "$CONFIG_FILE"
fi

require_command python3
require_command curl

REPRO_DIR="$PROJECT_ROOT/repro/quic-go-min-repro"
RUN_ID="${RUN_ID:-controlled-public-preflight-$(timestamp_utc)}"
ARTIFACT_DIR="${CONTROLLED_PUBLIC_PREFLIGHT_ARTIFACT_DIR:-$REPRO_DIR/artifacts/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
mkdir -p "$RESULT_DIR"

PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:-}"
PUBLIC_ORIGIN_NETWORK_CHANGE_URL="${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-$PUBLIC_ORIGIN_URL}"
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}"
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-}"
CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR:-${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-artifacts/controlled-public-h3-network-change-001}}"
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:-}"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
CONTROLLED_PUBLIC_READINESS_TIMEOUT="${CONTROLLED_PUBLIC_READINESS_TIMEOUT:-8}"

READINESS_JSON="$RESULT_DIR/controlled-public-experiment-readiness.json"
READINESS_MD="$RESULT_DIR/controlled-public-experiment-readiness.md"

READINESS_ARGS=(
  --public-origin-url "$PUBLIC_ORIGIN_NETWORK_CHANGE_URL"
  --baseline-summary "$CONTROLLED_PUBLIC_BASELINE_SUMMARY"
  --server-artifact-dir "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR"
  --network-change-cmd "$NETWORK_CHANGE_CMD"
  --chrome-bin "$CHROME_BIN"
  --timeout "$CONTROLLED_PUBLIC_READINESS_TIMEOUT"
)

echo "== Controlled public origin preflight =="
print_kv "config_file" "$CONFIG_FILE"
print_kv "config_present" "$CONFIG_PRESENT"
print_kv "run_id" "$RUN_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
print_kv "public_origin_url" "${PUBLIC_ORIGIN_URL:-}"
print_kv "network_change_url" "${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-}"
print_kv "baseline_summary" "${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}"
print_kv "server_artifact_dir" "${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-}"
print_kv "network_change_cmd_present" "$([[ -n "$NETWORK_CHANGE_CMD" ]] && echo true || echo false)"
echo

JSON_EXIT=0
python3 "$PROJECT_ROOT/tools/check_controlled_public_experiment_readiness.py" \
  "${READINESS_ARGS[@]}" \
  --format json \
  --output "$READINESS_JSON" || JSON_EXIT=$?

MARKDOWN_EXIT=0
python3 "$PROJECT_ROOT/tools/check_controlled_public_experiment_readiness.py" \
  "${READINESS_ARGS[@]}" \
  --format markdown \
  --output "$READINESS_MD" || MARKDOWN_EXIT=$?

if [[ -s "$READINESS_MD" ]]; then
  echo "== Readiness summary =="
  cat "$READINESS_MD"
fi

echo
echo "== Next commands =="
if [[ "$CONFIG_PRESENT" != "1" ]]; then
  echo "1. cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env"
  echo "2. Edit harness/config/controlled-public-origin.env with the public host, cert paths, baseline summary path, and network-change command."
else
  echo "server:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q PUBLIC_ORIGIN_HOST=%q TLS_CERT_FILE=%q TLS_KEY_FILE=%q PUBLIC_ORIGIN_PORT=%q EXPECTED_REQUESTS=%q ./scripts/run-controlled-public-h3-server.sh\n' \
    "${CONTROLLED_PUBLIC_BASELINE_RUN_ID:-controlled-public-chrome-h3-baseline-001}" \
    "${CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" \
    "${PUBLIC_ORIGIN_HOST:-h3.example.com}" \
    "${TLS_CERT_FILE:-/etc/letsencrypt/live/h3.example.com/fullchain.pem}" \
    "${TLS_KEY_FILE:-/etc/letsencrypt/live/h3.example.com/privkey.pem}" \
    "${PUBLIC_ORIGIN_PORT:-443}" \
    "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-4}"
  echo "baseline:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=%q REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 PUBLIC_ORIGIN_URL=%q CHROME_TIMEOUT_SECONDS=%q CHROME_VIRTUAL_TIME_BUDGET_MS=%q ./scripts/run-controlled-public-h3-browser-baseline.sh\n' \
    "${CONTROLLED_PUBLIC_BASELINE_RUN_ID:-controlled-public-chrome-h3-baseline-001}" \
    "${CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" \
    "${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" \
    "${PUBLIC_ORIGIN_URL:-https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow}" \
    "${CHROME_TIMEOUT_SECONDS:-30}" \
    "${CHROME_VIRTUAL_TIME_BUDGET_MS:-0}"
  echo "network-change:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=%q CONTROLLED_PUBLIC_BASELINE_SUMMARY=%q PUBLIC_ORIGIN_URL=%q NETWORK_CHANGE_AFTER_SECONDS=%q NETWORK_CHANGE_CMD=%q ./scripts/run-controlled-public-h3-network-change.sh\n' \
    "${CONTROLLED_PUBLIC_NETWORK_CHANGE_RUN_ID:-controlled-public-h3-network-change-001}" \
    "${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-artifacts/controlled-public-h3-network-change-001}" \
    "$CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR" \
    "${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json}" \
    "${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat}" \
    "${NETWORK_CHANGE_AFTER_SECONDS:-3}" \
    "${NETWORK_CHANGE_CMD:-}"
fi

echo
print_kv "readiness_json" "$READINESS_JSON"
print_kv "readiness_markdown" "$READINESS_MD"

if [[ "$JSON_EXIT" == "0" && "$MARKDOWN_EXIT" == "0" ]]; then
  echo "controlled_public_preflight=ready"
  exit 0
fi

echo "controlled_public_preflight=blocked"
exit 1
