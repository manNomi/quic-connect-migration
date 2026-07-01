#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-msquic-rebind-pathvalidation-demo-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

MSQUIC_DIR="${MSQUIC_DIR:-/private/tmp/quic-cm-scan-repos/msquic}"
MSQUIC_EXPECTED_COMMIT="${MSQUIC_EXPECTED_COMMIT:-51d449b7d2deb553d6503591f72a8e62d1071054}"
MSQUIC_BIN="${MSQUIC_BIN:-$MSQUIC_DIR/build-local/bin/Debug/msquictest}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_READY="${REQUIRE_READY:-0}"
DRY_RUN="${DRY_RUN:-0}"

FILTER_V4="${FILTER_V4:-Basic/WithFamilyArgs.RebindPort/0:Basic/WithFamilyArgs.RebindAddr/0:Basic/WithFamilyArgs.PathValidationTimeout/0:Basic/WithFamilyArgs.PathValidationLastPathClose/0}"
FILTER_V6="${FILTER_V6:-Basic/WithFamilyArgs.RebindPort/1:Basic/WithFamilyArgs.RebindAddr/1:Basic/WithFamilyArgs.PathValidationTimeout/1:Basic/WithFamilyArgs.PathValidationLastPathClose/1}"

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
    print_kv "msquic_dir" "$MSQUIC_DIR"
    print_kv "msquic_expected_commit" "$MSQUIC_EXPECTED_COMMIT"
    print_kv "msquic_observed_commit" "${MSQUIC_OBSERVED_COMMIT:-not-observed}"
    print_kv "msquic_commit_matches" "${MSQUIC_COMMIT_MATCHES:-unknown}"
    print_kv "msquic_bin" "$MSQUIC_BIN"
    print_kv "require_ready" "$REQUIRE_READY"
    print_kv "dry_run" "$DRY_RUN"
    print_kv "filter_v4" "$FILTER_V4"
    print_kv "filter_v6" "$FILTER_V6"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "msquictest_list_exit" "${MSQUICTEST_LIST_EXIT:-not-run}"
    print_kv "msquictest_v4_exit" "${MSQUICTEST_V4_EXIT:-not-run}"
    print_kv "msquictest_v6_exit" "${MSQUICTEST_V6_EXIT:-not-run}"
    print_kv "listed_rebind_pathvalidation_count" "${LISTED_REBIND_PATHVALIDATION_COUNT:-not-run}"
    print_kv "v4_ok_count" "${V4_OK_COUNT:-not-run}"
    print_kv "v6_ok_count" "${V6_OK_COUNT:-not-run}"
    print_kv "total_ok_count" "${TOTAL_OK_COUNT:-not-run}"
    print_kv "passed_summary_count" "${PASSED_SUMMARY_COUNT:-not-run}"
    print_kv "failed_marker_count" "${FAILED_MARKER_COUNT:-not-run}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# MsQuic Rebind Path Validation Demo Artifact

This artifact is public-safe. It records a fail-closed MsQuic user-mode selected rebind/path-validation test gate without storing credentials, private keys, keylogs, pcaps, NetLogs, hostnames, account identifiers, or raw packet captures in the tracked report.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| MsQuic dir | \`$MSQUIC_DIR\` |
| observed commit | \`${MSQUIC_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$MSQUIC_EXPECTED_COMMIT\` |
| commit matches | \`${MSQUIC_COMMIT_MATCHES:-unknown}\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert this artifact into browser, HTTP/3 application, CDN/LB, or production deployment evidence. A paper-ready local MsQuic row from this runner is limited to selected user-mode NAT rebind and path-validation tests.
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

count_fixed() {
  local pattern="$1"
  shift
  local count
  count="$(grep -Fhi "$pattern" "$@" 2>/dev/null | wc -l | tr -d ' ')"
  printf '%s' "$count"
}

if [[ ! -d "$MSQUIC_DIR" ]]; then
  fail_or_block "blocked" "missing_msquic_source_dir" "preflight"
fi

MSQUIC_OBSERVED_COMMIT="$(git -C "$MSQUIC_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$MSQUIC_OBSERVED_COMMIT" == "$MSQUIC_EXPECTED_COMMIT" ]]; then
  MSQUIC_COMMIT_MATCHES="yes"
else
  MSQUIC_COMMIT_MATCHES="no"
fi

if [[ "$MSQUIC_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "msquic_commit_mismatch" "preflight"
fi

MISSING=()
for command_name in git grep wc; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    MISSING+=("$command_name")
  fi
done
if [[ "${#MISSING[@]}" -gt 0 ]]; then
  PREFLIGHT_MISSING_COMMANDS="$(IFS=,; echo "${MISSING[*]}")"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi
PREFLIGHT_MISSING_COMMANDS="none"

if [[ ! -x "$MSQUIC_BIN" ]]; then
  fail_or_block "blocked" "missing_msquictest_binary" "preflight"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  write_result "blocked" "dry_run_only" "preflight"
  exit 0
fi

set +e
(
  cd "$MSQUIC_DIR"
  "$MSQUIC_BIN" --gtest_list_tests
) >"$LOG_DIR/msquictest-list.stdout" 2>"$LOG_DIR/msquictest-list.stderr"
MSQUICTEST_LIST_EXIT=$?
set -e

LISTED_REBIND_PATHVALIDATION_COUNT="$(
  count_fixed "RebindPort/" "$LOG_DIR/msquictest-list.stdout" "$LOG_DIR/msquictest-list.stderr"
)"
LISTED_REBIND_PATHVALIDATION_COUNT="$((LISTED_REBIND_PATHVALIDATION_COUNT + $(count_fixed "RebindAddr/" "$LOG_DIR/msquictest-list.stdout" "$LOG_DIR/msquictest-list.stderr") + $(count_fixed "PathValidationTimeout/" "$LOG_DIR/msquictest-list.stdout" "$LOG_DIR/msquictest-list.stderr") + $(count_fixed "PathValidationLastPathClose/" "$LOG_DIR/msquictest-list.stdout" "$LOG_DIR/msquictest-list.stderr")))"

set +e
(
  cd "$MSQUIC_DIR"
  "$MSQUIC_BIN" --gtest_filter="$FILTER_V4"
) >"$LOG_DIR/msquictest-v4.stdout" 2>"$LOG_DIR/msquictest-v4.stderr"
MSQUICTEST_V4_EXIT=$?
set -e

set +e
(
  cd "$MSQUIC_DIR"
  "$MSQUIC_BIN" --gtest_filter="$FILTER_V6"
) >"$LOG_DIR/msquictest-v6.stdout" 2>"$LOG_DIR/msquictest-v6.stderr"
MSQUICTEST_V6_EXIT=$?
set -e

V4_OK_COUNT="$(count_fixed "[       OK ] Basic/WithFamilyArgs." "$LOG_DIR/msquictest-v4.stdout" "$LOG_DIR/msquictest-v4.stderr")"
V6_OK_COUNT="$(count_fixed "[       OK ] Basic/WithFamilyArgs." "$LOG_DIR/msquictest-v6.stdout" "$LOG_DIR/msquictest-v6.stderr")"
TOTAL_OK_COUNT="$((V4_OK_COUNT + V6_OK_COUNT))"
PASSED_SUMMARY_COUNT="$(( $(count_fixed "[  PASSED  ] 4 tests." "$LOG_DIR/msquictest-v4.stdout" "$LOG_DIR/msquictest-v4.stderr") + $(count_fixed "[  PASSED  ] 4 tests." "$LOG_DIR/msquictest-v6.stdout" "$LOG_DIR/msquictest-v6.stderr") ))"
FAILED_MARKER_COUNT="$(( $(count_fixed "[  FAILED  ]" "$LOG_DIR/msquictest-v4.stdout" "$LOG_DIR/msquictest-v4.stderr") + $(count_fixed "[  FAILED  ]" "$LOG_DIR/msquictest-v6.stdout" "$LOG_DIR/msquictest-v6.stderr") ))"

if [[ "$MSQUICTEST_LIST_EXIT" == "0" \
  && "$MSQUICTEST_V4_EXIT" == "0" \
  && "$MSQUICTEST_V6_EXIT" == "0" \
  && "$LISTED_REBIND_PATHVALIDATION_COUNT" -ge 8 \
  && "$V4_OK_COUNT" == "4" \
  && "$V6_OK_COUNT" == "4" \
  && "$TOTAL_OK_COUNT" == "8" \
  && "$PASSED_SUMMARY_COUNT" == "2" \
  && "$FAILED_MARKER_COUNT" == "0" ]]; then
  write_result "ok" "none" "msquictest_selected_filters"
  exit 0
fi

if [[ "$MSQUICTEST_LIST_EXIT" != "0" ]]; then
  fail_or_block "failed" "msquictest_list_failed" "list_tests"
fi
if [[ "$MSQUICTEST_V4_EXIT" != "0" ]]; then
  fail_or_block "failed" "msquictest_v4_filter_failed" "v4_filter"
fi
if [[ "$MSQUICTEST_V6_EXIT" != "0" ]]; then
  fail_or_block "failed" "msquictest_v6_filter_failed" "v6_filter"
fi

fail_or_block "failed" "missing_msquic_rebind_or_pathvalidation_evidence" "msquictest_selected_filters"
