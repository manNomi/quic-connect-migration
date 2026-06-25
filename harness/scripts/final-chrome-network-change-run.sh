#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command python3

CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
if [[ -f "$CONFIG_FILE" ]]; then
  load_env_if_present "$CONFIG_FILE"
fi

REPRO_DIR="$PROJECT_ROOT/repro/quic-go-min-repro"
DEFAULT_TRIAL_ID="controlled-public-chrome-downlink-noheartbeat-network-change-001"
CONFIGURED_TRIAL_ID="${CONTROLLED_PUBLIC_NETWORK_CHANGE_RUN_ID:-$DEFAULT_TRIAL_ID}"
TRIAL_ID="${TRIAL_ID:-$CONFIGURED_TRIAL_ID}"
if [[ -z "${ARTIFACT_DIR:-}" ]]; then
  if [[ "$TRIAL_ID" == "$CONFIGURED_TRIAL_ID" && -n "${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-}" ]]; then
    ARTIFACT_DIR="$REPRO_DIR/$CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR"
  else
    ARTIFACT_DIR="$REPRO_DIR/artifacts/$TRIAL_ID"
  fi
fi
if [[ -z "${SERVER_ARTIFACT_DIR:-}" ]]; then
  if [[ "$TRIAL_ID" == "$CONFIGURED_TRIAL_ID" && -n "${CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR:-}" ]]; then
    SERVER_ARTIFACT_DIR="$CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR"
  elif [[ "$TRIAL_ID" == "$CONFIGURED_TRIAL_ID" && -n "${CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR:-}" ]]; then
    SERVER_ARTIFACT_DIR="$CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR"
  else
    SERVER_ARTIFACT_DIR="artifacts/$TRIAL_ID"
  fi
fi
BASELINE_ARTIFACT_DIR="${CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR:-artifacts/controlled-public-chrome-h3-baseline-001}"
BASELINE_ARTIFACT_DIR_ABS="${BASELINE_ARTIFACT_DIR}"
if [[ "$BASELINE_ARTIFACT_DIR_ABS" != /* ]]; then
  BASELINE_ARTIFACT_DIR_ABS="$REPRO_DIR/$BASELINE_ARTIFACT_DIR_ABS"
fi
REQUIREMENTS_CSV="${REQUIREMENTS_CSV:-$PROJECT_ROOT/data/final-browser-handover-required-trials.csv}"
OUTPUT_DIR="${FINAL_CHROME_NETWORK_CHANGE_RUN_OUTPUT_DIR:-$ARTIFACT_DIR/results/final-chrome-network-change-run-$(timestamp_utc)}"
NETWORK_CHANGE_RUNNER="${NETWORK_CHANGE_RUNNER:-$REPRO_DIR/scripts/run-controlled-public-h3-network-change.sh}"
RUN_POSTCHECKS="${RUN_POSTCHECKS:-1}"
CHECK_BASELINE_UNLOCK="${CHECK_BASELINE_UNLOCK:-1}"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_ROOT"

echo "== Final Chrome active network-change run =="
print_kv "config_file" "$CONFIG_FILE"
print_kv "trial_id" "$TRIAL_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
print_kv "server_artifact_dir" "$SERVER_ARTIFACT_DIR"
print_kv "baseline_artifact_dir" "$BASELINE_ARTIFACT_DIR_ABS"
print_kv "output_dir" "$OUTPUT_DIR"
print_kv "run_postchecks" "$RUN_POSTCHECKS"
print_kv "check_baseline_unlock" "$CHECK_BASELINE_UNLOCK"

OVERALL=0
CONFIG_READY=0
BASELINE_READY=0
RUN_OK=0

run_step() {
  local name="$1"
  local status
  shift
  echo
  echo "== $name =="
  if "$@"; then
    print_kv "$name" "ok"
    return 0
  else
    status="$?"
    print_kv "$name" "blocked(exit=$status)"
    OVERALL=1
    return "$status"
  fi
}

CONFIG_FLAGS=(--config "$CONFIG_FILE")
if [[ "${CHECK_LOCAL_FILES:-0}" == "1" ]]; then
  CONFIG_FLAGS+=(--check-files)
fi

if run_step "controlled_public_active_config" \
  python3 tools/check_controlled_public_config.py \
    "${CONFIG_FLAGS[@]}" \
    --output "$OUTPUT_DIR/controlled-public-config-check.md" \
    --require-active-ready; then
  CONFIG_READY=1
fi

if [[ "$CONFIG_READY" == "1" && "$CHECK_BASELINE_UNLOCK" == "1" ]]; then
  if run_step "baseline_unlock" \
    python3 tools/check_controlled_public_baseline_unlock.py \
      --artifact-dir "$BASELINE_ARTIFACT_DIR_ABS" \
      --requirements "$REQUIREMENTS_CSV" \
      --output "$OUTPUT_DIR/controlled-public-baseline-unlock-check.md" \
      --require-unlocked; then
    BASELINE_READY=1
  fi
elif [[ "$CONFIG_READY" == "1" ]]; then
  print_kv "baseline_unlock" "skipped(CHECK_BASELINE_UNLOCK=0)"
  BASELINE_READY=1
else
  print_kv "baseline_unlock" "skipped(config_not_ready)"
fi

if [[ "$CONFIG_READY" == "1" && "$BASELINE_READY" == "1" ]]; then
  if run_step "network_change_execution" \
    env \
      RUN_ID="$TRIAL_ID" \
      ARTIFACT_DIR="$ARTIFACT_DIR" \
      CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="$SERVER_ARTIFACT_DIR" \
      CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}" \
      PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-${PUBLIC_ORIGIN_URL:-}}" \
      CONTROLLED_PUBLIC_EXPECTED_REQUESTS="${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" \
      REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}" \
      REQUIRE_CONTROLLED_PUBLIC_BASELINE="${REQUIRE_CONTROLLED_PUBLIC_BASELINE:-1}" \
      CHROME_RUNNER="${CHROME_RUNNER:-cdp}" \
      CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-18}" \
      CHROME_BIN="${CHROME_BIN:-}" \
      CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-30}" \
      CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Default}" \
      CHROME_VIRTUAL_TIME_BUDGET_MS="${CHROME_VIRTUAL_TIME_BUDGET_MS:-0}" \
      NETWORK_CHANGE_AFTER_SECONDS="${NETWORK_CHANGE_AFTER_SECONDS:-3}" \
      NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:-}" \
      "$NETWORK_CHANGE_RUNNER"; then
    RUN_OK=1
  fi
else
  print_kv "network_change_execution" "skipped(readiness_not_met)"
fi

if [[ "$RUN_POSTCHECKS" == "1" && "$RUN_OK" == "1" ]]; then
  run_step "artifact_bundle_check" \
    python3 tools/check_final_handover_trial_artifact_bundle.py \
      --trial-id "$TRIAL_ID" \
      --artifact-dir "$ARTIFACT_DIR" \
      --requirements "$REQUIREMENTS_CSV" \
      --require-final-countable \
      --require-complete \
      --output "$OUTPUT_DIR/artifact-bundle-check.md"

  run_step "artifact_validation" \
    python3 tools/validate_final_handover_trial_artifact.py \
      --trial-id "$TRIAL_ID" \
      --artifact-dir "$ARTIFACT_DIR" \
      --requirements "$REQUIREMENTS_CSV" \
      --require-final-countable \
      --output "$OUTPUT_DIR/artifact-validation.md"
elif [[ "$RUN_POSTCHECKS" == "1" ]]; then
  print_kv "artifact_bundle_check" "skipped(network_change_not_ok)"
  print_kv "artifact_validation" "skipped(network_change_not_ok)"
else
  print_kv "artifact_bundle_check" "skipped(RUN_POSTCHECKS=0)"
  print_kv "artifact_validation" "skipped(RUN_POSTCHECKS=0)"
fi

echo
print_kv "network_change_run_artifacts" "$OUTPUT_DIR"
if [[ "$OVERALL" == "0" ]]; then
  echo "final_chrome_network_change_run=ready"
  exit 0
fi

echo "final_chrome_network_change_run=blocked"
exit 1
