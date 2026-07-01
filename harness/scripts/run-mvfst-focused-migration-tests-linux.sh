#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-mvfst-focused-migration-linux-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

MVFST_DIR="${MVFST_DIR:-/private/tmp/quic-cm-scan-repos/mvfst}"
MVFST_EXPECTED_COMMIT="${MVFST_EXPECTED_COMMIT:-d9d65a3ab3e6ffba785d6605afe6f05b8db015ec}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_LINUX="${REQUIRE_LINUX:-1}"
REQUIRE_READY="${REQUIRE_READY:-0}"
RUNNER_MODE="${RUNNER_MODE:-buck}"
DISK_THRESHOLD_GIB="${DISK_THRESHOLD_GIB:-30.0}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"

FOCUSED_TARGETS=(
  "quic/state/test:quic_path_manager_test"
  "quic/client/test:QuicClientTransportLiteMigrationTest"
  "quic/server/test:QuicServerTransportMigrationTest"
)

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
    print_kv "mvfst_dir" "$MVFST_DIR"
    print_kv "mvfst_expected_commit" "$MVFST_EXPECTED_COMMIT"
    print_kv "mvfst_observed_commit" "${MVFST_OBSERVED_COMMIT:-not-observed}"
    print_kv "mvfst_commit_matches" "${MVFST_COMMIT_MATCHES:-unknown}"
    print_kv "runner_mode" "$RUNNER_MODE"
    print_kv "require_linux" "$REQUIRE_LINUX"
    print_kv "jobs" "$JOBS"
    print_kv "disk_threshold_gib" "$DISK_THRESHOLD_GIB"
    print_kv "disk_free_gib" "${DISK_FREE_GIB:-not-observed}"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "focused_targets" "$(IFS=,; echo "${FOCUSED_TARGETS[*]}")"
    print_kv "buck_target_results" "${BUCK_TARGET_RESULTS:-not-run}"
    print_kv "buck_targets_passed" "${BUCK_TARGETS_PASSED:-0}"
    print_kv "buck_targets_failed" "${BUCK_TARGETS_FAILED:-0}"
    print_kv "getdeps_build_exit" "${GETDEPS_BUILD_EXIT:-not-run}"
    print_kv "getdeps_test_exit" "${GETDEPS_TEST_EXIT:-not-run}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# mvfst Focused Migration Linux Artifact

This artifact is public-safe. It records whether focused mvfst migration/path tests could be executed on the current host without storing credentials, private keys, qlogs, keylogs, pcaps, NetLogs, account identifiers, hostnames, or IP addresses.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| mvfst dir | \`$MVFST_DIR\` |
| observed commit | \`${MVFST_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$MVFST_EXPECTED_COMMIT\` |
| commit matches | \`${MVFST_COMMIT_MATCHES:-unknown}\` |
| runner mode | \`$RUNNER_MODE\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert a blocked artifact into a runtime PASS or FAIL claim. A paper-ready focused PASS requires all three BUCK targets to exit 0 in \`RUNNER_MODE=buck\`.
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

command_missing() {
  ! command -v "$1" >/dev/null 2>&1
}

safe_name_for_target() {
  printf '%s' "$1" | tr '/:' '__'
}

if [[ ! -d "$MVFST_DIR/quic" ]]; then
  fail_or_block "blocked" "missing_mvfst_source_dir" "preflight"
fi

MVFST_OBSERVED_COMMIT="$(git -C "$MVFST_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$MVFST_OBSERVED_COMMIT" == "$MVFST_EXPECTED_COMMIT" ]]; then
  MVFST_COMMIT_MATCHES="yes"
else
  MVFST_COMMIT_MATCHES="no"
fi

if [[ "$MVFST_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "mvfst_commit_mismatch" "preflight"
fi

if command_missing python3; then
  PREFLIGHT_MISSING_COMMANDS="python3"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi

DISK_FREE_GIB="$(python3 - "$MVFST_DIR" <<'PY'
import shutil
import sys
path = sys.argv[1]
usage = shutil.disk_usage(path)
print(round(usage.free / (1024 ** 3), 2))
PY
)"

DISK_READY="$(python3 - "$DISK_FREE_GIB" "$DISK_THRESHOLD_GIB" <<'PY'
import sys
print("yes" if float(sys.argv[1]) >= float(sys.argv[2]) else "no")
PY
)"

if [[ "$REQUIRE_LINUX" == "1" && "$SYSTEM_NAME" != "Linux" ]]; then
  fail_or_block "blocked" "linux_required" "preflight"
fi

if [[ "$DISK_READY" != "yes" ]]; then
  fail_or_block "blocked" "disk_below_threshold" "preflight"
fi

case "$RUNNER_MODE" in
  buck|getdeps)
    ;;
  *)
    fail_or_block "blocked" "unsupported_runner_mode" "preflight"
    ;;
esac

MISSING=()
if [[ "$RUNNER_MODE" == "buck" ]]; then
  for command_name in git buck2; do
    if command_missing "$command_name"; then
      MISSING+=("$command_name")
    fi
  done
else
  for command_name in git cmake ninja python3; do
    if command_missing "$command_name"; then
      MISSING+=("$command_name")
    fi
  done
fi

if [[ "${#MISSING[@]}" -gt 0 ]]; then
  PREFLIGHT_MISSING_COMMANDS="$(IFS=,; echo "${MISSING[*]}")"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi
PREFLIGHT_MISSING_COMMANDS="none"

for target in "${FOCUSED_TARGETS[@]}"; do
  target_name="${target##*:}"
  target_dir="${target%%:*}"
  if [[ ! -f "$MVFST_DIR/$target_dir/BUCK" ]]; then
    fail_or_block "blocked" "missing_buck_file_for_${target_name}" "preflight"
  fi
  if ! grep -q "name = \"$target_name\"" "$MVFST_DIR/$target_dir/BUCK"; then
    fail_or_block "blocked" "missing_buck_target_${target_name}" "preflight"
  fi
done

if [[ "$RUNNER_MODE" == "buck" ]]; then
  BUCK_TARGETS_PASSED=0
  BUCK_TARGETS_FAILED=0
  BUCK_TARGET_RESULTS=""
  for target in "${FOCUSED_TARGETS[@]}"; do
    safe_target="$(safe_name_for_target "$target")"
    set +e
    (
      cd "$MVFST_DIR"
      buck2 test "$target"
    ) >"$LOG_DIR/buck-${safe_target}.stdout" 2>"$LOG_DIR/buck-${safe_target}.stderr"
    target_exit=$?
    set -e
    if [[ -n "$BUCK_TARGET_RESULTS" ]]; then
      BUCK_TARGET_RESULTS="${BUCK_TARGET_RESULTS};"
    fi
    BUCK_TARGET_RESULTS="${BUCK_TARGET_RESULTS}${target}:${target_exit}"
    if [[ "$target_exit" == "0" ]]; then
      BUCK_TARGETS_PASSED=$((BUCK_TARGETS_PASSED + 1))
    else
      BUCK_TARGETS_FAILED=$((BUCK_TARGETS_FAILED + 1))
    fi
  done
  if [[ "$BUCK_TARGETS_FAILED" != "0" ]]; then
    fail_or_block "failed" "one_or_more_buck_targets_failed" "buck_test"
  fi
  write_result "ok" "none" "buck_test"
  exit 0
fi

if [[ ! -f "$MVFST_DIR/build/fbcode_builder/getdeps.py" ]]; then
  fail_or_block "blocked" "missing_getdeps_py" "preflight"
fi

set +e
(
  cd "$MVFST_DIR"
  python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs "$JOBS" build mvfst
) >"$LOG_DIR/getdeps-build.stdout" 2>"$LOG_DIR/getdeps-build.stderr"
GETDEPS_BUILD_EXIT=$?
set -e

if [[ "$GETDEPS_BUILD_EXIT" != "0" ]]; then
  fail_or_block "failed" "getdeps_build_failed" "getdeps_build"
fi

set +e
(
  cd "$MVFST_DIR"
  python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs "$JOBS" test mvfst
) >"$LOG_DIR/getdeps-test.stdout" 2>"$LOG_DIR/getdeps-test.stderr"
GETDEPS_TEST_EXIT=$?
set -e

if [[ "$GETDEPS_TEST_EXIT" != "0" ]]; then
  fail_or_block "failed" "getdeps_test_failed" "getdeps_test"
fi

write_result "ok" "none" "getdeps_test"
