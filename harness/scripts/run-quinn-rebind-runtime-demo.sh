#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-quinn-rebind-runtime-demo-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

QUINN_DIR="${QUINN_DIR:-/private/tmp/quic-cm-scan-repos/quinn}"
QUINN_EXPECTED_COMMIT="${QUINN_EXPECTED_COMMIT:-953b466747e667a9dfda0596b8051a0644f8333d}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_READY="${REQUIRE_READY:-0}"
DRY_RUN="${DRY_RUN:-0}"
QUINN_FEATURES="${QUINN_FEATURES:-rustls-ring}"
QUINN_REBIND_RUST_LOG="${QUINN_REBIND_RUST_LOG:-info}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

SYSTEM_NAME="$(uname -s)"
SYSTEM_MACHINE="$(uname -m)"

write_result() {
  local validation="$1"
  local reason="$2"
  local stage="${3:-preflight}"
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "system_name" "$SYSTEM_NAME"
    print_kv "system_machine" "$SYSTEM_MACHINE"
    print_kv "quinn_dir" "$QUINN_DIR"
    print_kv "quinn_expected_commit" "$QUINN_EXPECTED_COMMIT"
    print_kv "quinn_observed_commit" "${QUINN_OBSERVED_COMMIT:-not-observed}"
    print_kv "quinn_commit_matches" "${QUINN_COMMIT_MATCHES:-unknown}"
    print_kv "require_ready" "$REQUIRE_READY"
    print_kv "dry_run" "$DRY_RUN"
    print_kv "quinn_features" "$QUINN_FEATURES"
    print_kv "quinn_rebind_rust_log" "$QUINN_REBIND_RUST_LOG"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "cargo_quinn_rebind_exit" "${CARGO_QUINN_REBIND_EXIT:-not-run}"
    print_kv "cargo_quinn_proto_migration_exit" "${CARGO_QUINN_PROTO_MIGRATION_EXIT:-not-run}"
    print_kv "rebind_recv_ok_count" "${REBIND_RECV_OK_COUNT:-not-run}"
    print_kv "connected_log_count" "${CONNECTED_LOG_COUNT:-not-run}"
    print_kv "got_conn_log_count" "${GOT_CONN_LOG_COUNT:-not-run}"
    print_kv "rebound_log_count" "${REBOUND_LOG_COUNT:-not-run}"
    print_kv "proto_migration_ok_count" "${PROTO_MIGRATION_OK_COUNT:-not-run}"
    print_kv "proto_migration_initiated_count" "${PROTO_MIGRATION_INITIATED_COUNT:-not-run}"
    print_kv "path_challenge_count" "${PATH_CHALLENGE_COUNT:-not-run}"
    print_kv "path_response_count" "${PATH_RESPONSE_COUNT:-not-run}"
    print_kv "new_path_validated_count" "${NEW_PATH_VALIDATED_COUNT:-not-run}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# Quinn Rebind Runtime Demo Artifact

This artifact is public-safe. It records a fail-closed Quinn endpoint rebind and proto migration gate without storing credentials, private keys, keylogs, pcaps, NetLogs, hostnames, account identifiers, or raw packet captures in the tracked report.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| Quinn dir | \`$QUINN_DIR\` |
| observed commit | \`${QUINN_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$QUINN_EXPECTED_COMMIT\` |
| commit matches | \`${QUINN_COMMIT_MATCHES:-unknown}\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert this artifact into browser, HTTP/3, CDN, or managed deployment evidence. A paper-ready local Quinn runtime row requires the endpoint rebind test to pass, the stream receive logs to appear, and the proto migration test to show migration/path-validation evidence.
EOF
}

fail_or_block() {
  local validation="$1"
  local reason="$2"
  local stage="${3:-preflight}"
  write_result "$validation" "$reason" "$stage"
  if [[ "$validation" == "blocked" && "$REQUIRE_READY" != "1" ]]; then
    exit 0
  fi
  exit 1
}

count_text() {
  local pattern="$1"
  shift
  local count
  count="$(grep -ERhi "$pattern" "$@" 2>/dev/null | wc -l | tr -d ' ')"
  printf '%s' "$count"
}

if [[ ! -d "$QUINN_DIR" ]]; then
  fail_or_block "blocked" "missing_quinn_source_dir" "preflight"
fi

QUINN_OBSERVED_COMMIT="$(git -C "$QUINN_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$QUINN_OBSERVED_COMMIT" == "$QUINN_EXPECTED_COMMIT" ]]; then
  QUINN_COMMIT_MATCHES="yes"
else
  QUINN_COMMIT_MATCHES="no"
fi

if [[ "$QUINN_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "quinn_commit_mismatch" "preflight"
fi

MISSING=()
for command_name in git cargo rustc; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    MISSING+=("$command_name")
  fi
done
if [[ "${#MISSING[@]}" -gt 0 ]]; then
  PREFLIGHT_MISSING_COMMANDS="$(IFS=,; echo "${MISSING[*]}")"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi
PREFLIGHT_MISSING_COMMANDS="none"

if [[ "$DRY_RUN" == "1" ]]; then
  write_result "blocked" "dry_run_only" "preflight"
  exit 0
fi

FEATURE_ARGS=()
if [[ -n "$QUINN_FEATURES" ]]; then
  FEATURE_ARGS=(--features "$QUINN_FEATURES")
fi

set +e
(
  cd "$QUINN_DIR"
  RUST_LOG="$QUINN_REBIND_RUST_LOG" cargo test -p quinn rebind_recv "${FEATURE_ARGS[@]}" -- --nocapture
) >"$LOG_DIR/quinn-rebind-recv.stdout" 2>"$LOG_DIR/quinn-rebind-recv.stderr"
CARGO_QUINN_REBIND_EXIT=$?
set -e

set +e
(
  cd "$QUINN_DIR"
  cargo test -p quinn-proto migration -- --nocapture
) >"$LOG_DIR/quinn-proto-migration.stdout" 2>"$LOG_DIR/quinn-proto-migration.stderr"
CARGO_QUINN_PROTO_MIGRATION_EXIT=$?
set -e

REBIND_RECV_OK_COUNT="$(count_text "test tests::rebind_recv .* ok" "$LOG_DIR/quinn-rebind-recv.stdout" "$LOG_DIR/quinn-rebind-recv.stderr")"
CONNECTED_LOG_COUNT="$(count_text "connected" "$LOG_DIR/quinn-rebind-recv.stdout" "$LOG_DIR/quinn-rebind-recv.stderr")"
GOT_CONN_LOG_COUNT="$(count_text "got conn" "$LOG_DIR/quinn-rebind-recv.stdout" "$LOG_DIR/quinn-rebind-recv.stderr")"
REBOUND_LOG_COUNT="$(count_text "rebound" "$LOG_DIR/quinn-rebind-recv.stdout" "$LOG_DIR/quinn-rebind-recv.stderr")"
PROTO_MIGRATION_OK_COUNT="$(count_text "test tests::migration .* ok" "$LOG_DIR/quinn-proto-migration.stdout" "$LOG_DIR/quinn-proto-migration.stderr")"
PROTO_MIGRATION_INITIATED_COUNT="$(count_text "migration initiated" "$LOG_DIR/quinn-proto-migration.stdout" "$LOG_DIR/quinn-proto-migration.stderr")"
PATH_CHALLENGE_COUNT="$(count_text "PATH_CHALLENGE|PathChallenge" "$LOG_DIR/quinn-proto-migration.stdout" "$LOG_DIR/quinn-proto-migration.stderr")"
PATH_RESPONSE_COUNT="$(count_text "PATH_RESPONSE|PathResponse" "$LOG_DIR/quinn-proto-migration.stdout" "$LOG_DIR/quinn-proto-migration.stderr")"
NEW_PATH_VALIDATED_COUNT="$(count_text "new path validated" "$LOG_DIR/quinn-proto-migration.stdout" "$LOG_DIR/quinn-proto-migration.stderr")"

if [[ "$CARGO_QUINN_REBIND_EXIT" == "0" \
  && "$CARGO_QUINN_PROTO_MIGRATION_EXIT" == "0" \
  && "$REBIND_RECV_OK_COUNT" != "0" \
  && "$CONNECTED_LOG_COUNT" != "0" \
  && "$GOT_CONN_LOG_COUNT" != "0" \
  && "$REBOUND_LOG_COUNT" != "0" \
  && "$PROTO_MIGRATION_OK_COUNT" != "0" \
  && "$PROTO_MIGRATION_INITIATED_COUNT" != "0" \
  && "$PATH_CHALLENGE_COUNT" != "0" \
  && "$PATH_RESPONSE_COUNT" != "0" \
  && "$NEW_PATH_VALIDATED_COUNT" != "0" ]]; then
  write_result "ok" "none" "cargo_tests"
  exit 0
fi

if [[ "$CARGO_QUINN_REBIND_EXIT" != "0" ]]; then
  fail_or_block "failed" "quinn_rebind_recv_failed" "cargo_quinn_rebind"
fi
if [[ "$CARGO_QUINN_PROTO_MIGRATION_EXIT" != "0" ]]; then
  fail_or_block "failed" "quinn_proto_migration_failed" "cargo_quinn_proto_migration"
fi

fail_or_block "failed" "missing_quinn_rebind_or_path_validation_evidence" "cargo_tests"
