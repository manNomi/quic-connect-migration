#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command python3

TRIAL_ID="${TRIAL_ID:-${FINAL_HANDOVER_TRIAL_ID:-controlled-public-chrome-h3-baseline-001}}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/repro/quic-go-min-repro/artifacts/$TRIAL_ID}"
EXPERIMENTS_CSV="${EXPERIMENTS_CSV:-$PROJECT_ROOT/data/experiment-results.csv}"
REQUIREMENTS_CSV="${REQUIREMENTS_CSV:-$PROJECT_ROOT/data/final-browser-handover-required-trials.csv}"
APPLY="${APPLY:-0}"

if [[ -d "$ARTIFACT_DIR" ]]; then
  DEFAULT_OUTPUT_DIR="$ARTIFACT_DIR/results/registration-$(timestamp_utc)"
else
  DEFAULT_OUTPUT_DIR="$PROJECT_ROOT/repro/quic-go-min-repro/artifacts/final-registration-$TRIAL_ID-$(timestamp_utc)/results"
fi
OUTPUT_DIR="${FINAL_HANDOVER_REGISTRATION_OUTPUT_DIR:-$DEFAULT_OUTPUT_DIR}"
mkdir -p "$OUTPUT_DIR"

cd "$PROJECT_ROOT"

echo "== Final handover result registration =="
print_kv "trial_id" "$TRIAL_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
print_kv "experiments_csv" "$EXPERIMENTS_CSV"
print_kv "requirements_csv" "$REQUIREMENTS_CSV"
print_kv "output_dir" "$OUTPUT_DIR"
print_kv "apply" "$APPLY"

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

run_step "append_dry_run" \
  python3 tools/append_final_handover_result_row.py \
    --trial-id "$TRIAL_ID" \
    --artifact-dir "$ARTIFACT_DIR" \
    --experiments "$EXPERIMENTS_CSV" \
    --requirements "$REQUIREMENTS_CSV" \
    --require-final-countable \
    --require-artifact-bundle \
    --output "$OUTPUT_DIR/append-dry-run.md"

if [[ "$APPLY" == "1" ]]; then
  run_step "append_apply" \
    python3 tools/append_final_handover_result_row.py \
      --trial-id "$TRIAL_ID" \
      --artifact-dir "$ARTIFACT_DIR" \
      --experiments "$EXPERIMENTS_CSV" \
      --requirements "$REQUIREMENTS_CSV" \
      --require-final-countable \
      --require-artifact-bundle \
      --apply \
      --output "$OUTPUT_DIR/append-apply.md"

  run_step "final_trial_audit" \
    python3 tools/audit_final_browser_handover_trials.py \
      --experiments "$EXPERIMENTS_CSV" \
      --requirements "$REQUIREMENTS_CSV" \
      --output "$OUTPUT_DIR/final-browser-handover-trial-audit.md"
else
  echo
  print_kv "append_apply" "skipped(set APPLY=1 to append)"
fi

echo
print_kv "registration_artifacts" "$OUTPUT_DIR"
if [[ "$OVERALL" == "0" ]]; then
  if [[ "$APPLY" == "1" ]]; then
    echo "final_handover_registration=applied"
  else
    echo "final_handover_registration=dry_run_ready"
  fi
  exit 0
fi

echo "final_handover_registration=blocked"
exit 1
