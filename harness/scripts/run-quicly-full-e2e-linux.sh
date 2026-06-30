#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-quicly-full-e2e-linux-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

QUICLY_DIR="${QUICLY_DIR:-/private/tmp/quic-cm-scan-repos/quicly}"
QUICLY_EXPECTED_COMMIT="${QUICLY_EXPECTED_COMMIT:-ed83c7c7d545a01650651c9523466f561ec5d4bb}"
QUICLY_BUILD_DIR="${QUICLY_BUILD_DIR:-$QUICLY_DIR/build-linux-full-e2e}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_LINUX="${REQUIRE_LINUX:-1}"
REQUIRE_READY="${REQUIRE_READY:-0}"
REQUIRE_FULL_E2E="${REQUIRE_FULL_E2E:-1}"
UPDATE_SUBMODULES="${UPDATE_SUBMODULES:-1}"
CMAKE_GENERATOR="${CMAKE_GENERATOR:-Ninja}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

SYSTEM_NAME="$(uname -s)"
SYSTEM_MACHINE="$(uname -m)"
E2E_T="$QUICLY_DIR/t/e2e.t"

write_result() {
  local validation="$1"
  local reason="$2"
  local stage="${3:-preflight}"
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "system_name" "$SYSTEM_NAME"
    print_kv "system_machine" "$SYSTEM_MACHINE"
    print_kv "quicly_dir" "$QUICLY_DIR"
    print_kv "quicly_expected_commit" "$QUICLY_EXPECTED_COMMIT"
    print_kv "quicly_observed_commit" "${QUICLY_OBSERVED_COMMIT:-not-observed}"
    print_kv "quicly_commit_matches" "${QUICLY_COMMIT_MATCHES:-unknown}"
    print_kv "quicly_build_dir" "$QUICLY_BUILD_DIR"
    print_kv "require_linux" "$REQUIRE_LINUX"
    print_kv "require_full_e2e" "$REQUIRE_FULL_E2E"
    print_kv "update_submodules" "$UPDATE_SUBMODULES"
    print_kv "cmake_generator" "$CMAKE_GENERATOR"
    print_kv "jobs" "$JOBS"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "net_empty_port_ready" "${NET_EMPTY_PORT_READY:-not-run}"
    print_kv "submodule_update_exit" "${SUBMODULE_UPDATE_EXIT:-not-run}"
    print_kv "cmake_configure_exit" "${CMAKE_CONFIGURE_EXIT:-not-run}"
    print_kv "cmake_build_exit" "${CMAKE_BUILD_EXIT:-not-run}"
    print_kv "unit_test_exit" "${UNIT_TEST_EXIT:-not-run}"
    print_kv "prove_exit" "${PROVE_EXIT:-not-run}"
    print_kv "path_subtest_seen" "${PATH_SUBTEST_SEEN:-not-run}"
    print_kv "path_subtest_ok" "${PATH_SUBTEST_OK:-not-run}"
    print_kv "cid_seq_check_ok" "${CID_SEQ_CHECK_OK:-not-run}"
    print_kv "slow_start_failed" "${SLOW_START_FAILED:-not-run}"
    print_kv "result_fail" "${RESULT_FAIL:-not-run}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# quicly Full e2e Linux Artifact

This artifact is public-safe. It records a fail-closed quicly full e2e replay gate without storing credentials, private keys, qlogs, keylogs, pcaps, NetLogs, hostnames, or account identifiers.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| quicly dir | \`$QUICLY_DIR\` |
| observed commit | \`${QUICLY_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$QUICLY_EXPECTED_COMMIT\` |
| commit matches | \`${QUICLY_COMMIT_MATCHES:-unknown}\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert a blocked or partial artifact into full e2e PASS evidence. A paper-ready full PASS requires \`unit_test_exit=0\`, \`prove_exit=0\`, \`path_subtest_ok=yes\`, and \`cid_seq_check_ok=yes\`.
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

if [[ ! -d "$QUICLY_DIR" ]]; then
  fail_or_block "blocked" "missing_quicly_source_dir" "preflight"
fi

QUICLY_OBSERVED_COMMIT="$(git -C "$QUICLY_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$QUICLY_OBSERVED_COMMIT" == "$QUICLY_EXPECTED_COMMIT" ]]; then
  QUICLY_COMMIT_MATCHES="yes"
else
  QUICLY_COMMIT_MATCHES="no"
fi

if [[ "$QUICLY_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "quicly_commit_mismatch" "preflight"
fi

if [[ "$REQUIRE_LINUX" == "1" && "$SYSTEM_NAME" != "Linux" ]]; then
  fail_or_block "blocked" "linux_required" "preflight"
fi

MISSING=()
for command_name in git cmake perl prove python3 cc; do
  if command_missing "$command_name"; then
    MISSING+=("$command_name")
  fi
done
if [[ "$CMAKE_GENERATOR" == "Ninja" ]] && command_missing ninja; then
  MISSING+=("ninja")
fi

if [[ "${#MISSING[@]}" -gt 0 ]]; then
  PREFLIGHT_MISSING_COMMANDS="$(IFS=,; echo "${MISSING[*]}")"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi
PREFLIGHT_MISSING_COMMANDS="none"

if [[ ! -f "$E2E_T" ]]; then
  fail_or_block "blocked" "missing_e2e_t" "preflight"
fi

PERL_LIB_PATHS=()
if [[ -n "${QUICLY_PERL5LIB:-}" ]]; then
  PERL_LIB_PATHS+=("$QUICLY_PERL5LIB")
elif [[ -n "${PERL5LIB:-}" ]]; then
  PERL_LIB_PATHS+=("$PERL5LIB")
fi
if [[ -d /private/tmp/quic-cm-perl5/lib/perl5 ]]; then
  PERL_LIB_PATHS+=("/private/tmp/quic-cm-perl5/lib/perl5")
fi
PERL_LIB_PATHS+=("$QUICLY_DIR")
JOINED_PERL5LIB="$(IFS=:; echo "${PERL_LIB_PATHS[*]}")"

if env PERL5LIB="$JOINED_PERL5LIB" perl -MNet::EmptyPort -e 'print "ok\n"' >"$LOG_DIR/perl-net-empty-port-check.txt" 2>&1; then
  NET_EMPTY_PORT_READY="yes"
else
  NET_EMPTY_PORT_READY="no"
  fail_or_block "blocked" "missing_perl_net_empty_port" "preflight"
fi

if [[ "$UPDATE_SUBMODULES" == "1" ]]; then
  set +e
  (
    cd "$QUICLY_DIR"
    git submodule update --init --recursive
  ) >"$LOG_DIR/submodule-update.stdout" 2>"$LOG_DIR/submodule-update.stderr"
  SUBMODULE_UPDATE_EXIT=$?
  set -e
  if [[ "$SUBMODULE_UPDATE_EXIT" != "0" ]]; then
    fail_or_block "failed" "submodule_update_failed" "submodule_update"
  fi
fi

set +e
cmake -S "$QUICLY_DIR" -B "$QUICLY_BUILD_DIR" -G "$CMAKE_GENERATOR" \
  -DCMAKE_BUILD_TYPE=Debug \
  -DWITH_DTRACE=OFF \
  -DWITH_FUSION=OFF \
  >"$LOG_DIR/cmake-configure.stdout" \
  2>"$LOG_DIR/cmake-configure.stderr"
CMAKE_CONFIGURE_EXIT=$?
set -e

if [[ "$CMAKE_CONFIGURE_EXIT" != "0" ]]; then
  fail_or_block "failed" "cmake_configure_failed" "cmake_configure"
fi

set +e
cmake --build "$QUICLY_BUILD_DIR" --target test.t cli udpfw -j "$JOBS" \
  >"$LOG_DIR/cmake-build.stdout" \
  2>"$LOG_DIR/cmake-build.stderr"
CMAKE_BUILD_EXIT=$?
set -e

if [[ "$CMAKE_BUILD_EXIT" != "0" ]]; then
  fail_or_block "failed" "cmake_build_failed" "cmake_build"
fi

set +e
"$QUICLY_BUILD_DIR/test.t" \
  >"$LOG_DIR/unit-test.stdout" \
  2>"$LOG_DIR/unit-test.stderr"
UNIT_TEST_EXIT=$?
set -e

set +e
(
  cd "$QUICLY_DIR" && \
    env BINARY_DIR="$QUICLY_BUILD_DIR" PERL5LIB="$JOINED_PERL5LIB" prove -v t/e2e.t
) >"$LOG_DIR/prove-e2e.log" 2>&1
PROVE_EXIT=$?
set -e

PATH_SUBTEST_SEEN="no"
PATH_SUBTEST_OK="no"
CID_SEQ_CHECK_OK="no"
SLOW_START_FAILED="no"
RESULT_FAIL="no"

if grep -q '# Subtest: path-migration' "$LOG_DIR/prove-e2e.log"; then
  PATH_SUBTEST_SEEN="yes"
fi
if grep -q 'ok [0-9][0-9]* - path-migration' "$LOG_DIR/prove-e2e.log"; then
  PATH_SUBTEST_OK="yes"
fi
if grep -q 'ok [0-9][0-9]* - CID seq 1 is used for 1st path probe' "$LOG_DIR/prove-e2e.log"; then
  CID_SEQ_CHECK_OK="yes"
fi
if grep -q 'not ok [0-9][0-9]* - slow-start' "$LOG_DIR/prove-e2e.log"; then
  SLOW_START_FAILED="yes"
fi
if grep -q 'Result: FAIL' "$LOG_DIR/prove-e2e.log"; then
  RESULT_FAIL="yes"
fi

python3 - "$LOG_DIR/prove-e2e.log" "$RESULT_DIR/path-migration-excerpt.txt" <<'PY'
from pathlib import Path
import sys

log_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
lines = log_path.read_text(errors="ignore").splitlines()
start = None
for idx, line in enumerate(lines):
    if "# Subtest: path-migration" in line:
        start = max(0, idx - 5)
        break
if start is None:
    out_path.write_text("path-migration subtest not found\n")
    raise SystemExit(0)
end = min(len(lines), start + 100)
out_path.write_text("\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end)) + "\n")
PY

if [[ "$UNIT_TEST_EXIT" == "0" && "$PROVE_EXIT" == "0" && "$PATH_SUBTEST_OK" == "yes" && "$CID_SEQ_CHECK_OK" == "yes" ]]; then
  write_result "ok_full_e2e" "none" "prove_e2e"
  exit 0
fi

if [[ "$PATH_SUBTEST_OK" == "yes" && "$CID_SEQ_CHECK_OK" == "yes" && "$REQUIRE_FULL_E2E" != "1" ]]; then
  write_result "ok_path_migration_only" "full_e2e_not_clean" "prove_e2e"
  exit 0
fi

write_result "failed" "full_e2e_or_unit_not_clean" "prove_e2e"
exit 1
