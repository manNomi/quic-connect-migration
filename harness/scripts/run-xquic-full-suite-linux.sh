#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-xquic-full-suite-linux-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

XQUIC_DIR="${XQUIC_DIR:-/private/tmp/quic-cm-scan-repos/xquic}"
XQUIC_EXPECTED_COMMIT="${XQUIC_EXPECTED_COMMIT:-96155cffbde7f062fe45ac3f6899f47e25709d30}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_LINUX="${REQUIRE_LINUX:-1}"
REQUIRE_READY="${REQUIRE_READY:-0}"
RUN_CASE_TESTS="${RUN_CASE_TESTS:-1}"
DRY_RUN="${DRY_RUN:-0}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)}"

BUILD_DIR="${BUILD_DIR:-$XQUIC_DIR/build}"
BORINGSSL_DIR="${BORINGSSL_DIR:-$XQUIC_DIR/third_party/boringssl}"

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
    print_kv "xquic_dir" "$XQUIC_DIR"
    print_kv "xquic_expected_commit" "$XQUIC_EXPECTED_COMMIT"
    print_kv "xquic_observed_commit" "${XQUIC_OBSERVED_COMMIT:-not-observed}"
    print_kv "xquic_commit_matches" "${XQUIC_COMMIT_MATCHES:-unknown}"
    print_kv "require_linux" "$REQUIRE_LINUX"
    print_kv "run_case_tests" "$RUN_CASE_TESTS"
    print_kv "dry_run" "$DRY_RUN"
    print_kv "jobs" "$JOBS"
    print_kv "build_dir" "$BUILD_DIR"
    print_kv "boringssl_dir" "$BORINGSSL_DIR"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "boringssl_build_exit" "${BORINGSSL_BUILD_EXIT:-not-run}"
    print_kv "xquic_configure_exit" "${XQUIC_CONFIGURE_EXIT:-not-run}"
    print_kv "xquic_build_exit" "${XQUIC_BUILD_EXIT:-not-run}"
    print_kv "run_tests_exit" "${RUN_TESTS_EXIT:-not-run}"
    print_kv "case_tests_exit" "${CASE_TESTS_EXIT:-not-run}"
    print_kv "unit_test_passed_count" "${UNIT_TEST_PASSED_COUNT:-not-observed}"
    print_kv "unit_test_failed_count" "${UNIT_TEST_FAILED_COUNT:-not-observed}"
    print_kv "case_test_pass_count" "${CASE_TEST_PASS_COUNT:-not-observed}"
    print_kv "case_test_fail_count" "${CASE_TEST_FAIL_COUNT:-not-observed}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# XQUIC Full-suite Linux Artifact

This artifact is public-safe. It records the XQUIC full-suite Linux replay gate without storing credentials, private keys, qlogs, keylogs, pcaps, NetLogs, or account identifiers.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| XQUIC dir | \`$XQUIC_DIR\` |
| observed commit | \`${XQUIC_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$XQUIC_EXPECTED_COMMIT\` |
| commit matches | \`${XQUIC_COMMIT_MATCHES:-unknown}\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert a blocked artifact into a runtime PASS or FAIL claim. A paper-ready PASS requires \`run_tests_exit=0\`, \`case_tests_exit=0\` when case tests are enabled, and zero observed failed test markers.
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

count_filtered_matches() {
  local first_pattern="$1"
  local second_pattern="$2"
  shift 2
  local count
  count="$( ( { grep -h "$first_pattern" "$@" 2>/dev/null || true; } | grep -c "$second_pattern" ) || true )"
  printf '%s' "$count" | tr -d ' '
}

if [[ ! -d "$XQUIC_DIR" ]]; then
  fail_or_block "blocked" "missing_xquic_source_dir" "preflight"
fi

XQUIC_OBSERVED_COMMIT="$(git -C "$XQUIC_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$XQUIC_OBSERVED_COMMIT" == "$XQUIC_EXPECTED_COMMIT" ]]; then
  XQUIC_COMMIT_MATCHES="yes"
else
  XQUIC_COMMIT_MATCHES="no"
fi

if [[ "$XQUIC_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "xquic_commit_mismatch" "preflight"
fi

if [[ "$REQUIRE_LINUX" == "1" && "$SYSTEM_NAME" != "Linux" ]]; then
  fail_or_block "blocked" "linux_required" "preflight"
fi

MISSING=()
for command_name in cmake git make openssl python3 cc c++; do
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

mkdir -p "$BUILD_DIR" "$(dirname "$BORINGSSL_DIR")"

if [[ ! -f "$BORINGSSL_DIR/CMakeLists.txt" ]]; then
  if [[ -e "$BORINGSSL_DIR" && -n "$(find "$BORINGSSL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]]; then
    fail_or_block "blocked" "boringssl_dir_exists_but_is_not_source" "preflight"
  fi
  set +e
  git clone --depth 1 https://github.com/google/boringssl.git "$BORINGSSL_DIR" \
    >"$LOG_DIR/boringssl-clone.stdout" \
    2>"$LOG_DIR/boringssl-clone.stderr"
  BORINGSSL_CLONE_EXIT=$?
  set -e
  if [[ "$BORINGSSL_CLONE_EXIT" != "0" ]]; then
    fail_or_block "failed" "boringssl_clone_failed" "boringssl_clone"
  fi
fi

mkdir -p "$BORINGSSL_DIR/build"
set +e
cmake -S "$BORINGSSL_DIR" -B "$BORINGSSL_DIR/build" \
  -DBUILD_SHARED_LIBS=0 \
  -DCMAKE_C_FLAGS="-fPIC" \
  -DCMAKE_CXX_FLAGS="-fPIC" \
  >"$LOG_DIR/boringssl-configure.stdout" \
  2>"$LOG_DIR/boringssl-configure.stderr"
BORINGSSL_CONFIGURE_EXIT=$?
if [[ "$BORINGSSL_CONFIGURE_EXIT" == "0" ]]; then
  cmake --build "$BORINGSSL_DIR/build" --target ssl crypto -j "$JOBS" \
    >"$LOG_DIR/boringssl-build.stdout" \
    2>"$LOG_DIR/boringssl-build.stderr"
  BORINGSSL_BUILD_EXIT=$?
else
  BORINGSSL_BUILD_EXIT="$BORINGSSL_CONFIGURE_EXIT"
fi
set -e

if [[ "$BORINGSSL_BUILD_EXIT" != "0" ]]; then
  fail_or_block "failed" "boringssl_build_failed" "boringssl_build"
fi

set +e
cmake -S "$XQUIC_DIR" -B "$BUILD_DIR" \
  -DGCOV=off \
  -DCMAKE_BUILD_TYPE=Debug \
  -DXQC_ENABLE_TESTING=1 \
  -DXQC_PRINT_SECRET=0 \
  -DXQC_SUPPORT_SENDMMSG_BUILD=1 \
  -DXQC_ENABLE_EVENT_LOG=1 \
  -DXQC_ENABLE_BBR2=1 \
  -DXQC_ENABLE_RENO=1 \
  -DSSL_TYPE=boringssl \
  -DSSL_PATH="$BORINGSSL_DIR" \
  -DXQC_ENABLE_UNLIMITED=1 \
  -DXQC_ENABLE_COPA=1 \
  -DXQC_COMPAT_DUPLICATE=1 \
  >"$LOG_DIR/xquic-configure.stdout" \
  2>"$LOG_DIR/xquic-configure.stderr"
XQUIC_CONFIGURE_EXIT=$?
set -e

if [[ "$XQUIC_CONFIGURE_EXIT" != "0" ]]; then
  fail_or_block "failed" "xquic_configure_failed" "xquic_configure"
fi

set +e
cmake --build "$BUILD_DIR" --target run_tests test_client test_server -j "$JOBS" \
  >"$LOG_DIR/xquic-build.stdout" \
  2>"$LOG_DIR/xquic-build.stderr"
XQUIC_BUILD_EXIT=$?
set -e

if [[ "$XQUIC_BUILD_EXIT" != "0" ]]; then
  fail_or_block "failed" "xquic_build_failed" "xquic_build"
fi

(
  cd "$BUILD_DIR"
  if [[ ! -f server.key || ! -f server.crt ]]; then
    openssl req -newkey rsa:2048 -x509 -nodes \
      -keyout server.key \
      -new \
      -out server.crt \
      -subj /CN=test.xquic.com \
      >"$LOG_DIR/openssl-cert.stdout" \
      2>"$LOG_DIR/openssl-cert.stderr"
  fi
)

set +e
"$BUILD_DIR/tests/run_tests" \
  >"$LOG_DIR/run-tests.stdout" \
  2>"$LOG_DIR/run-tests.stderr"
RUN_TESTS_EXIT=$?
set -e

if [[ "$RUN_CASE_TESTS" == "1" ]]; then
  set +e
  (
    cd "$BUILD_DIR"
    sh "$XQUIC_DIR/scripts/case_test.sh"
  ) >"$LOG_DIR/case-tests.stdout" 2>"$LOG_DIR/case-tests.stderr"
  CASE_TESTS_EXIT=$?
  set -e
else
  CASE_TESTS_EXIT="skipped"
fi

UNIT_TEST_PASSED_COUNT="$(count_filtered_matches "Test:" "passed" "$LOG_DIR/run-tests.stdout" "$LOG_DIR/run-tests.stderr")"
UNIT_TEST_FAILED_COUNT="$(count_filtered_matches "Test:" "FAILED" "$LOG_DIR/run-tests.stdout" "$LOG_DIR/run-tests.stderr")"
CASE_TEST_PASS_COUNT="$(count_filtered_matches "pass:" "pass:1" "$LOG_DIR/case-tests.stdout" "$LOG_DIR/case-tests.stderr")"
CASE_TEST_FAIL_COUNT="$(count_filtered_matches "pass:" "pass:0" "$LOG_DIR/case-tests.stdout" "$LOG_DIR/case-tests.stderr")"

if [[ "$RUN_TESTS_EXIT" != "0" ]]; then
  fail_or_block "failed" "run_tests_failed" "run_tests"
fi

if [[ "$RUN_CASE_TESTS" == "1" && "$CASE_TESTS_EXIT" != "0" ]]; then
  fail_or_block "failed" "case_tests_failed" "case_tests"
fi

if [[ "$UNIT_TEST_FAILED_COUNT" != "0" || "$CASE_TEST_FAIL_COUNT" != "0" ]]; then
  fail_or_block "failed" "failed_test_markers_observed" "classification"
fi

write_result "ok" "none" "classification"
