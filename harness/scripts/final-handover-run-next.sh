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
OUTPUT_DIR="${FINAL_HANDOVER_RUN_NEXT_OUTPUT_DIR:-$REPRO_DIR/artifacts/final-handover-run-next-$(timestamp_utc)/results}"
READINESS_JSON="${FINAL_HANDOVER_RUN_NEXT_READINESS_JSON:-$OUTPUT_DIR/next-trial-readiness.json}"
READINESS_MD="${FINAL_HANDOVER_RUN_NEXT_READINESS_MD:-$OUTPUT_DIR/next-trial-readiness.md}"
RUNNER_LOG="${FINAL_HANDOVER_RUN_NEXT_RUNNER_LOG:-$OUTPUT_DIR/runner.log}"
RUN_POSTCHECKS="${RUN_POSTCHECKS:-1}"
USE_LOCAL_CONFIG_FOR_PLAN="${USE_LOCAL_CONFIG_FOR_PLAN:-1}"
REDACT_SENSITIVE="${REDACT_SENSITIVE:-1}"
FINAL_HANDOVER_MIN_DISK_GIB="${FINAL_HANDOVER_MIN_DISK_GIB:-7}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-$FINAL_HANDOVER_MIN_DISK_GIB}"

FINAL_P0_BASELINE_WRAPPER="${FINAL_P0_BASELINE_WRAPPER:-$SCRIPT_DIR/final-p0-baseline-run.sh}"
FINAL_CHROME_NOCHANGE_WRAPPER="${FINAL_CHROME_NOCHANGE_WRAPPER:-$SCRIPT_DIR/final-chrome-nochange-run.sh}"
FINAL_CHROME_NETWORK_CHANGE_WRAPPER="${FINAL_CHROME_NETWORK_CHANGE_WRAPPER:-$SCRIPT_DIR/final-chrome-network-change-run.sh}"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_ROOT"

json_value() {
  local path="$1"
  python3 - "$READINESS_JSON" "$path" <<'PY'
import json
import sys

data = json.loads(open(sys.argv[1], encoding="utf-8").read())
value = data
for part in sys.argv[2].split("."):
    if not part:
        continue
    if value is None:
        break
    value = value.get(part) if isinstance(value, dict) else None
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, list):
    print(";".join(str(item) for item in value))
elif value is None:
    print("")
else:
    print(value)
PY
}

echo "== Final handover run-next dispatcher =="
print_kv "config_file" "$CONFIG_FILE"
print_kv "output_dir" "$OUTPUT_DIR"
print_kv "readiness_json" "$READINESS_JSON"
print_kv "run_postchecks" "$RUN_POSTCHECKS"
print_kv "use_local_config_for_plan" "$USE_LOCAL_CONFIG_FOR_PLAN"
print_kv "redact_sensitive" "$REDACT_SENSITIVE"
print_kv "final_handover_min_disk_gib" "$FINAL_HANDOVER_MIN_DISK_GIB"
print_kv "min_artifact_free_gib" "$MIN_ARTIFACT_FREE_GIB"

READINESS_COMMON_ARGS=(
  --config "$CONFIG_FILE"
  --min-disk-gib "$FINAL_HANDOVER_MIN_DISK_GIB"
)
if [[ "$USE_LOCAL_CONFIG_FOR_PLAN" == "1" ]]; then
  READINESS_COMMON_ARGS+=(--use-local-config-for-plan)
fi
if [[ "$REDACT_SENSITIVE" == "1" ]]; then
  READINESS_COMMON_ARGS+=(--redact-sensitive)
fi

if [[ -n "${FINAL_HANDOVER_RUN_NEXT_READINESS_FIXTURE:-}" ]]; then
  cp "$FINAL_HANDOVER_RUN_NEXT_READINESS_FIXTURE" "$READINESS_JSON"
else
  READINESS_ARGS=(
    "${READINESS_COMMON_ARGS[@]}"
    --format json
    --output "$READINESS_JSON"
  )
  set +e
  python3 tools/check_next_final_handover_trial_readiness.py "${READINESS_ARGS[@]}"
  READINESS_STATUS="$?"
  set -e
  print_kv "readiness_exit" "$READINESS_STATUS"
fi

python3 tools/check_next_final_handover_trial_readiness.py \
  "${READINESS_COMMON_ARGS[@]}" \
  --format markdown \
  --output "$READINESS_MD" >/dev/null || true

READY="$(json_value ready)"
TRIAL_ID="$(json_value next_trial.trial_id)"
PHASE="$(json_value next_trial.phase)"
BROWSER="$(json_value next_trial.browser)"
EXPECTED_REQUESTS="$(json_value next_trial.expected_requests)"
MISSING_GATES="$(json_value missing_required_gates)"

print_kv "ready" "$READY"
print_kv "trial_id" "${TRIAL_ID:--}"
print_kv "phase" "${PHASE:--}"
print_kv "browser" "${BROWSER:--}"
print_kv "expected_requests" "${EXPECTED_REQUESTS:--}"
print_kv "missing_gates" "${MISSING_GATES:--}"

if [[ "$READY" != "true" ]]; then
  echo "final_handover_run_next=blocked"
  exit 1
fi

if [[ -z "$TRIAL_ID" || -z "$PHASE" || -z "$BROWSER" ]]; then
  print_kv "dispatch" "blocked(no_next_trial)"
  echo "final_handover_run_next=blocked"
  exit 1
fi

case "$BROWSER:$PHASE" in
  "Chrome:baseline")
    print_kv "dispatch" "final-p0-baseline-run"
    env \
      TRIAL_ID="$TRIAL_ID" \
      CONTROLLED_PUBLIC_EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
      MIN_ARTIFACT_FREE_GIB="$MIN_ARTIFACT_FREE_GIB" \
      RUN_POSTCHECKS="$RUN_POSTCHECKS" \
      "$FINAL_P0_BASELINE_WRAPPER" | tee "$RUNNER_LOG"
    ;;
  "Chrome:no-change-baseline")
    print_kv "dispatch" "final-chrome-nochange-run"
    env \
      TRIAL_ID="$TRIAL_ID" \
      CONTROLLED_PUBLIC_EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
      MIN_ARTIFACT_FREE_GIB="$MIN_ARTIFACT_FREE_GIB" \
      RUN_POSTCHECKS="$RUN_POSTCHECKS" \
      "$FINAL_CHROME_NOCHANGE_WRAPPER" | tee "$RUNNER_LOG"
    ;;
  "Chrome:active-network-change")
    print_kv "dispatch" "final-chrome-network-change-run"
    env \
      TRIAL_ID="$TRIAL_ID" \
      CONTROLLED_PUBLIC_EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
      MIN_ARTIFACT_FREE_GIB="$MIN_ARTIFACT_FREE_GIB" \
      RUN_POSTCHECKS="$RUN_POSTCHECKS" \
      "$FINAL_CHROME_NETWORK_CHANGE_WRAPPER" | tee "$RUNNER_LOG"
    ;;
  *)
    print_kv "dispatch" "blocked(unsupported_${BROWSER}_${PHASE})"
    echo "final_handover_run_next=blocked"
    exit 2
    ;;
esac

echo "final_handover_run_next=ready"
