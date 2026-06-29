#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

USER_NETWORK_CHANGE_CMD_SET=0
USER_NETWORK_CHANGE_CMD=""
if [[ ${NETWORK_CHANGE_CMD+x} ]]; then
  USER_NETWORK_CHANGE_CMD_SET=1
  USER_NETWORK_CHANGE_CMD="$NETWORK_CHANGE_CMD"
fi
USER_ALLOW_LATENT_SECONDARY_PATH_SET=0
USER_ALLOW_LATENT_SECONDARY_PATH=""
if [[ ${ALLOW_LATENT_SECONDARY_PATH+x} ]]; then
  USER_ALLOW_LATENT_SECONDARY_PATH_SET=1
  USER_ALLOW_LATENT_SECONDARY_PATH="$ALLOW_LATENT_SECONDARY_PATH"
fi
USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH_SET=0
USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH=""
if [[ ${CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH+x} ]]; then
  USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH_SET=1
  USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH="$CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH"
fi

load_harness_env

CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
CONFIG_PRESENT=0
if [[ -f "$CONFIG_FILE" ]]; then
  CONFIG_PRESENT=1
  load_env_if_present "$CONFIG_FILE"
fi
if [[ "$USER_NETWORK_CHANGE_CMD_SET" == "1" ]]; then
  NETWORK_CHANGE_CMD="$USER_NETWORK_CHANGE_CMD"
fi
if [[ "$USER_ALLOW_LATENT_SECONDARY_PATH_SET" == "1" ]]; then
  ALLOW_LATENT_SECONDARY_PATH="$USER_ALLOW_LATENT_SECONDARY_PATH"
fi
if [[ "$USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH_SET" == "1" ]]; then
  CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH="$USER_CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH"
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
CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR:-${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001}}"
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:-}"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
CONTROLLED_PUBLIC_READINESS_TIMEOUT="${CONTROLLED_PUBLIC_READINESS_TIMEOUT:-8}"
REDACT_SENSITIVE="${REDACT_SENSITIVE:-1}"
ALLOW_LATENT_SECONDARY_PATH="${ALLOW_LATENT_SECONDARY_PATH:-${CONTROLLED_PUBLIC_ALLOW_LATENT_SECONDARY_PATH:-0}}"

preview_value() {
  local value="${1:-}"
  if [[ "$REDACT_SENSITIVE" == "1" && -n "$value" ]]; then
    printf '<configured>'
  else
    printf '%s' "$value"
  fi
}

redacted_arg() {
  local value="${1:-}"
  local placeholder="${2:-<configured>}"
  if [[ "$REDACT_SENSITIVE" == "1" && -n "$value" ]]; then
    printf '%s' "$placeholder"
  else
    printf '%s' "$value"
  fi
}

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

if [[ "$REDACT_SENSITIVE" == "1" ]]; then
  READINESS_ARGS+=(--redact-sensitive)
fi
if [[ "$ALLOW_LATENT_SECONDARY_PATH" == "1" ]]; then
  READINESS_ARGS+=(--allow-latent-secondary-path)
fi

echo "== Controlled public origin preflight =="
print_kv "config_file" "$CONFIG_FILE"
print_kv "config_present" "$CONFIG_PRESENT"
print_kv "redact_sensitive" "$REDACT_SENSITIVE"
print_kv "run_id" "$RUN_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
print_kv "public_origin_url" "$(preview_value "${PUBLIC_ORIGIN_URL:-}")"
print_kv "network_change_url" "$(preview_value "${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-}")"
print_kv "baseline_summary" "$(preview_value "${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}")"
print_kv "server_artifact_dir" "$(preview_value "${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-}")"
print_kv "network_change_cmd_present" "$([[ -n "$NETWORK_CHANGE_CMD" ]] && echo true || echo false)"
print_kv "allow_latent_secondary_path" "$ALLOW_LATENT_SECONDARY_PATH"
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
  echo "1. bash harness/scripts/init-controlled-public-config.sh"
  echo "2. Edit harness/config/controlled-public-origin.env with the public host, cert paths, baseline summary path, and network-change command."
else
  echo "server:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q PUBLIC_ORIGIN_HOST=%q TLS_CERT_FILE=%q TLS_KEY_FILE=%q PUBLIC_ORIGIN_PORT=%q EXPECTED_REQUESTS=%q ./scripts/run-controlled-public-h3-server.sh\n' \
    "${CONTROLLED_PUBLIC_BASELINE_RUN_ID:-controlled-public-chrome-h3-baseline-001}" \
    "${CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" \
    "$(redacted_arg "${PUBLIC_ORIGIN_HOST:-h3.example.com}" "<redacted-public-origin-host>")" \
    "$(redacted_arg "${TLS_CERT_FILE:-/etc/letsencrypt/live/h3.example.com/fullchain.pem}" "<redacted-tls-cert-file>")" \
    "$(redacted_arg "${TLS_KEY_FILE:-/etc/letsencrypt/live/h3.example.com/privkey.pem}" "<redacted-tls-key-file>")" \
    "${PUBLIC_ORIGIN_PORT:-443}" \
    "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-4}"
  echo "baseline:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=%q REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 PUBLIC_ORIGIN_URL=%q CHROME_TIMEOUT_SECONDS=%q CHROME_VIRTUAL_TIME_BUDGET_MS=%q ./scripts/run-controlled-public-h3-browser-baseline.sh\n' \
    "${CONTROLLED_PUBLIC_BASELINE_RUN_ID:-controlled-public-chrome-h3-baseline-001}" \
    "${CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" \
    "$(redacted_arg "${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}" "<redacted-server-artifact-dir>")" \
    "$(redacted_arg "${PUBLIC_ORIGIN_URL:-https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow}" "<redacted-public-origin-url>")" \
    "${CHROME_TIMEOUT_SECONDS:-30}" \
    "${CHROME_VIRTUAL_TIME_BUDGET_MS:-0}"
  echo "network-change:"
  printf '  cd %q\n' "$REPRO_DIR"
  printf '  RUN_ID=%q ARTIFACT_DIR=%q CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=%q CONTROLLED_PUBLIC_BASELINE_SUMMARY=%q PUBLIC_ORIGIN_URL=%q NETWORK_CHANGE_AFTER_SECONDS=%q NETWORK_CHANGE_CMD=%q ./scripts/run-controlled-public-h3-network-change.sh\n' \
    "${CONTROLLED_PUBLIC_NETWORK_CHANGE_RUN_ID:-controlled-public-chrome-downlink-noheartbeat-network-change-001}" \
    "${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001}" \
    "$(redacted_arg "$CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR" "<redacted-network-change-server-artifact-dir>")" \
    "$(redacted_arg "${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json}" "<redacted-baseline-summary>")" \
    "$(redacted_arg "${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat}" "<redacted-public-origin-network-change-url>")" \
    "${NETWORK_CHANGE_AFTER_SECONDS:-3}" \
    "$(redacted_arg "${NETWORK_CHANGE_CMD:-}" "<redacted-network-change-cmd>")"
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
