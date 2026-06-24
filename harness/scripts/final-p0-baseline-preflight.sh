#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command python3

CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
MATRIX="${FINAL_PROTOCOL_READINESS_MATRIX:-$PROJECT_ROOT/data/final-protocol-readiness-matrix-20260624.csv}"
SCORECARD="${FINAL_TRIAL_ACCEPTANCE_SCORECARD:-$PROJECT_ROOT/data/final-trial-acceptance-scorecard-20260624.csv}"
RUN_ID="${RUN_ID:-final-p0-baseline-preflight-$(timestamp_utc)}"
OUTPUT_DIR="${FINAL_P0_PREFLIGHT_OUTPUT_DIR:-$PROJECT_ROOT/repro/quic-go-min-repro/artifacts/$RUN_ID/results}"
TIMEOUT="${CONTROLLED_PUBLIC_READINESS_TIMEOUT:-8}"

CONFIG_FLAGS=(--config "$CONFIG_FILE")
READINESS_FLAGS=(--config "$CONFIG_FILE" --timeout "$TIMEOUT")
P0_FLAGS=(--config "$CONFIG_FILE" --matrix "$MATRIX" --scorecard "$SCORECARD")

if [[ "${CHECK_LOCAL_FILES:-0}" == "1" ]]; then
  CONFIG_FLAGS+=(--check-files)
  READINESS_FLAGS+=(--check-local-files)
fi

if [[ "${CHECK_PUBLIC_ORIGIN:-0}" == "1" ]]; then
  READINESS_FLAGS+=(--check-public-origin)
fi

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_ROOT"

echo "== Final P0 baseline preflight =="
print_kv "config_file" "$CONFIG_FILE"
print_kv "matrix" "$MATRIX"
print_kv "scorecard" "$SCORECARD"
print_kv "output_dir" "$OUTPUT_DIR"
print_kv "check_local_files" "${CHECK_LOCAL_FILES:-0}"
print_kv "check_public_origin" "${CHECK_PUBLIC_ORIGIN:-0}"

OVERALL=0

run_step() {
  local name="$1"
  shift
  echo
  echo "== $name =="
  if "$@"; then
    print_kv "$name" "ok"
  else
    local status="$?"
    print_kv "$name" "blocked(exit=$status)"
    OVERALL=1
  fi
}

run_step "controlled_public_config" \
  python3 tools/check_controlled_public_config.py \
    "${CONFIG_FLAGS[@]}" \
    --output "$OUTPUT_DIR/controlled-public-config-check.md" \
    --require-baseline-ready

run_step "next_trial_selection" \
  python3 tools/select_next_final_handover_trial.py \
    --output "$OUTPUT_DIR/final-handover-next-trial.md"

run_step "next_trial_readiness" \
  python3 tools/check_next_final_handover_trial_readiness.py \
    "${READINESS_FLAGS[@]}" \
    --output "$OUTPUT_DIR/final-handover-next-trial-readiness.md"

run_step "operator_checklist" \
  python3 tools/build_final_handover_operator_checklist.py \
    --output "$OUTPUT_DIR/final-handover-operator-checklist.md"

run_step "p0_baseline_preflight_guard" \
  python3 tools/check_p0_baseline_preflight.py \
    "${P0_FLAGS[@]}" \
    --output "$OUTPUT_DIR/p0-baseline-preflight-check.md" \
    --csv-output "$OUTPUT_DIR/p0-baseline-preflight-check.csv" \
    --require-go

echo
print_kv "preflight_artifacts" "$OUTPUT_DIR"
if [[ "$OVERALL" == "0" ]]; then
  echo "final_p0_baseline_preflight=ready"
  exit 0
fi

echo "final_p0_baseline_preflight=blocked"
exit 1
