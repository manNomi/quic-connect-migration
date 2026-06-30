#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
RUN_ID="${RUN_ID:-s2n-nlb-live-readiness-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"
LOCAL_PROOF_RESULT_DIR="${LOCAL_PROOF_RESULT_DIR:-$ARTIFACT_DIR/local-s2n-proof}"
RUN_LOCAL_PROOF="${RUN_LOCAL_PROOF:-1}"
REQUIRE_READY="${REQUIRE_READY:-0}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

if [[ -n "${AWS_PROFILE:-}" ]]; then
  export AWS_PROFILE
fi
export AWS_REGION
export AWS_DEFAULT_REGION="$AWS_REGION"

command_found() {
  command -v "$1" >/dev/null 2>&1
}

json_value() {
  local path="$1"
  local expr="$2"
  python3 - "$path" "$expr" <<'PY'
import json
import sys

path, expr = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(path, encoding="utf-8"))
except FileNotFoundError:
    print("")
    raise SystemExit(0)

value = data
for part in expr.split("."):
    if not part:
        continue
    if isinstance(value, dict):
        value = value.get(part, "")
    else:
        value = ""
        break
if isinstance(value, bool):
    print("yes" if value else "no")
elif value is None:
    print("")
else:
    print(value)
PY
}

write_result() {
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "aws_region" "$AWS_REGION"
    print_kv "aws_identity_ok" "$AWS_IDENTITY_OK"
    print_kv "aws_identity_classification" "$AWS_IDENTITY_CLASSIFICATION"
    print_kv "aws_cli_found" "$AWS_CLI_FOUND"
    print_kv "cargo_found" "$CARGO_FOUND"
    print_kv "local_proof_status" "$LOCAL_PROOF_STATUS"
    print_kv "local_proof_exit" "$LOCAL_PROOF_EXIT"
    print_kv "local_proof_echo_matches" "$LOCAL_PROOF_ECHO_MATCHES"
    print_kv "cid_provider_crate_ready" "$CID_PROVIDER_CRATE_READY"
    print_kv "existing_quic_go_nlb_runner_ready" "$QUIC_GO_NLB_RUNNER_READY"
    print_kv "s2n_live_nlb_runner_ready" "$S2N_LIVE_NLB_RUNNER_READY"
    print_kv "can_run_live_s2n_nlb_now" "$CAN_RUN_LIVE_S2N_NLB_NOW"
    print_kv "blocked_reason" "$BLOCKED_REASON"
    print_kv "aws_identity_markdown" "$RESULT_DIR/aws-identity-readiness.md"
    print_kv "aws_identity_json" "$RESULT_DIR/aws-identity-readiness.json"
    print_kv "local_proof_result_dir" "$LOCAL_PROOF_RESULT_DIR"
  } | tee "$RESULT_DIR/result.env"
}

AWS_CLI_FOUND="no"
if command_found aws; then
  AWS_CLI_FOUND="yes"
fi
CARGO_FOUND="no"
if command_found cargo; then
  CARGO_FOUND="yes"
fi

set +e
python3 "$PROJECT_ROOT/tools/check_aws_identity_readiness.py" \
  --region "$AWS_REGION" \
  --include-redacted-diagnostics \
  --output "$RESULT_DIR/aws-identity-readiness.md" \
  --json-output "$RESULT_DIR/aws-identity-readiness.json" \
  >"$LOG_DIR/aws-identity-readiness.stdout" \
  2>"$LOG_DIR/aws-identity-readiness.stderr"
AWS_READINESS_EXIT=$?
set -e

AWS_IDENTITY_OK="$(json_value "$RESULT_DIR/aws-identity-readiness.json" "identity_ok")"
AWS_IDENTITY_CLASSIFICATION="$(json_value "$RESULT_DIR/aws-identity-readiness.json" "classification")"
if [[ -z "$AWS_IDENTITY_OK" ]]; then
  AWS_IDENTITY_OK="no"
fi
if [[ -z "$AWS_IDENTITY_CLASSIFICATION" ]]; then
  AWS_IDENTITY_CLASSIFICATION="unknown"
fi

CID_PROVIDER_CRATE_READY="no"
if [[ -f "$PROJECT_ROOT/experiments/s2n-quic-nlb-cid-provider/Cargo.toml" ]]; then
  CID_PROVIDER_CRATE_READY="yes"
fi

LOCAL_PROOF_STATUS="skipped"
LOCAL_PROOF_EXIT="0"
LOCAL_PROOF_ECHO_MATCHES="unknown"
if [[ "$RUN_LOCAL_PROOF" == "1" ]]; then
  if [[ "$CID_PROVIDER_CRATE_READY" != "yes" ]]; then
    LOCAL_PROOF_STATUS="blocked_missing_crate"
    LOCAL_PROOF_EXIT="2"
  elif [[ "$CARGO_FOUND" != "yes" ]]; then
    LOCAL_PROOF_STATUS="blocked_missing_cargo"
    LOCAL_PROOF_EXIT="2"
  else
    set +e
    "$SCRIPT_DIR/run-local-s2n-nlb-cid-proof.sh" "$LOCAL_PROOF_RESULT_DIR" \
      >"$LOG_DIR/local-s2n-proof.stdout" \
      2>"$LOG_DIR/local-s2n-proof.stderr"
    LOCAL_PROOF_EXIT=$?
    set -e
    if [[ "$LOCAL_PROOF_EXIT" == "0" ]]; then
      LOCAL_PROOF_STATUS="$(json_value "$LOCAL_PROOF_RESULT_DIR/result.json" "status")"
      LOCAL_PROOF_ECHO_MATCHES="$(json_value "$LOCAL_PROOF_RESULT_DIR/result.json" "quic_echo.echo_matches")"
    else
      LOCAL_PROOF_STATUS="failed"
    fi
  fi
fi

QUIC_GO_NLB_RUNNER_READY="no"
if [[ -x "$SCRIPT_DIR/run-aws-nlb-quic-data-plane.sh" ]]; then
  QUIC_GO_NLB_RUNNER_READY="yes"
fi

S2N_LIVE_NLB_RUNNER_READY="no"
if [[ -x "$SCRIPT_DIR/run-aws-s2n-nlb-live-data-plane.sh" ]]; then
  S2N_LIVE_NLB_RUNNER_READY="yes"
fi

CAN_RUN_LIVE_S2N_NLB_NOW="yes"
BLOCKED_REASON="none"
if [[ "$AWS_IDENTITY_OK" != "yes" ]]; then
  CAN_RUN_LIVE_S2N_NLB_NOW="no"
  BLOCKED_REASON="aws_identity_${AWS_IDENTITY_CLASSIFICATION}"
elif [[ "$LOCAL_PROOF_STATUS" != "PASS" || "$LOCAL_PROOF_ECHO_MATCHES" != "yes" ]]; then
  CAN_RUN_LIVE_S2N_NLB_NOW="no"
  BLOCKED_REASON="local_s2n_cid_provider_proof_not_passed"
elif [[ "$S2N_LIVE_NLB_RUNNER_READY" != "yes" ]]; then
  CAN_RUN_LIVE_S2N_NLB_NOW="no"
  BLOCKED_REASON="s2n_live_nlb_runner_not_implemented"
fi

write_result

cat >"$RESULT_DIR/README.md" <<EOF
# s2n NLB Live Readiness Artifact

This artifact is public-safe. It records whether the repository can proceed to a live AWS NLB + s2n-quic data-plane experiment without iPhone input.

## Summary

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| AWS identity ok | \`$AWS_IDENTITY_OK\` |
| AWS identity classification | \`$AWS_IDENTITY_CLASSIFICATION\` |
| local s2n CID provider proof | \`$LOCAL_PROOF_STATUS\` |
| local proof echo matches | \`$LOCAL_PROOF_ECHO_MATCHES\` |
| existing quic-go NLB runner | \`$QUIC_GO_NLB_RUNNER_READY\` |
| s2n live NLB runner | \`$S2N_LIVE_NLB_RUNNER_READY\` |
| can run live s2n NLB now | \`$CAN_RUN_LIVE_S2N_NLB_NOW\` |
| blocked reason | \`$BLOCKED_REASON\` |

## Interpretation

- \`aws_identity_ok=no\` blocks any live AWS resource creation.
- \`local_proof_status=PASS\` only proves the local custom CID provider and echo endpoint; it is not an AWS NLB forwarding result.
- \`s2n_live_nlb_runner_ready=no\` means the existing live NLB runner still covers the quic-go path, while a dedicated s2n live target runner remains future work.
EOF

if [[ "$REQUIRE_READY" == "1" && "$CAN_RUN_LIVE_S2N_NLB_NOW" != "yes" ]]; then
  exit 1
fi

if [[ "$AWS_READINESS_EXIT" != "0" ]]; then
  exit 0
fi
