#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-ngtcp2-example-migration-demo-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"

NGTCP2_DIR="${NGTCP2_DIR:-/private/tmp/quic-cm-scan-repos/ngtcp2}"
NGTCP2_EXPECTED_COMMIT="${NGTCP2_EXPECTED_COMMIT:-c24b12690c5bdf7ad2715ae427504e76bf5c6ffc}"
BUILD_DIR="${BUILD_DIR:-$NGTCP2_DIR/build-example-migration}"
ALLOW_COMMIT_MISMATCH="${ALLOW_COMMIT_MISMATCH:-0}"
REQUIRE_READY="${REQUIRE_READY:-0}"
DRY_RUN="${DRY_RUN:-0}"
CMAKE_GENERATOR="${CMAKE_GENERATOR:-Ninja}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
PORT="${PORT:-44330}"
CHANGE_LOCAL_ADDR_AFTER="${CHANGE_LOCAL_ADDR_AFTER:-1ms}"
PAYLOAD_SIZE_BYTES="${PAYLOAD_SIZE_BYTES:-4194304}"
CLIENT_TIMEOUT_SECONDS="${CLIENT_TIMEOUT_SECONDS:-20}"
SERVER_STARTUP_SECONDS="${SERVER_STARTUP_SECONDS:-1}"
CLIENT_EXTRA_ARGS="${CLIENT_EXTRA_ARGS:-}"
LIBEV_INCLUDE_DIR="${LIBEV_INCLUDE_DIR:-}"
LIBEV_LIBRARY="${LIBEV_LIBRARY:-}"
UPDATE_SUBMODULES="${UPDATE_SUBMODULES:-1}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

SYSTEM_NAME="$(uname -s)"
SYSTEM_MACHINE="$(uname -m)"
SERVER_PID=""

cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

pkg_version() {
  local module="$1"
  if pkg-config --modversion "$module" >/dev/null 2>&1; then
    pkg-config --modversion "$module" 2>/dev/null | head -n 1
  elif [[ "$module" == "libev" ]]; then
    if [[ -n "$LIBEV_INCLUDE_DIR" && -n "$LIBEV_LIBRARY" && -f "$LIBEV_INCLUDE_DIR/ev.h" && -f "$LIBEV_LIBRARY" ]]; then
      awk '/EV_VERSION_MAJOR/ {major=$3} /EV_VERSION_MINOR/ {minor=$3} END {if (major && minor) print major "." minor; else print "present-no-pkg-config"}' "$LIBEV_INCLUDE_DIR/ev.h"
    else
      printf 'missing'
    fi
  else
    printf 'missing'
  fi
}

detect_libev_fallback() {
  if [[ -z "$LIBEV_INCLUDE_DIR" && -f /opt/homebrew/opt/libev/include/ev.h ]]; then
    LIBEV_INCLUDE_DIR="/opt/homebrew/opt/libev/include"
  fi
  if [[ -z "$LIBEV_LIBRARY" && -f /opt/homebrew/opt/libev/lib/libev.dylib ]]; then
    LIBEV_LIBRARY="/opt/homebrew/opt/libev/lib/libev.dylib"
  fi
}

write_result() {
  local validation="$1"
  local reason="$2"
  local stage="${3:-preflight}"
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "system_name" "$SYSTEM_NAME"
    print_kv "system_machine" "$SYSTEM_MACHINE"
    print_kv "ngtcp2_dir" "$NGTCP2_DIR"
    print_kv "ngtcp2_expected_commit" "$NGTCP2_EXPECTED_COMMIT"
    print_kv "ngtcp2_observed_commit" "${NGTCP2_OBSERVED_COMMIT:-not-observed}"
    print_kv "ngtcp2_commit_matches" "${NGTCP2_COMMIT_MATCHES:-unknown}"
    print_kv "build_dir" "$BUILD_DIR"
    print_kv "require_ready" "$REQUIRE_READY"
    print_kv "dry_run" "$DRY_RUN"
    print_kv "update_submodules" "$UPDATE_SUBMODULES"
    print_kv "cmake_generator" "$CMAKE_GENERATOR"
    print_kv "jobs" "$JOBS"
    print_kv "port" "$PORT"
    print_kv "change_local_addr_after" "$CHANGE_LOCAL_ADDR_AFTER"
    print_kv "payload_size_bytes" "$PAYLOAD_SIZE_BYTES"
    print_kv "preflight_missing_commands" "${PREFLIGHT_MISSING_COMMANDS:-none}"
    print_kv "pkg_config_libev" "${PKG_LIBEV:-not-run}"
    print_kv "libev_include_dir" "${LIBEV_INCLUDE_DIR:-not-set}"
    print_kv "libev_library" "${LIBEV_LIBRARY:-not-set}"
    print_kv "pkg_config_libnghttp3" "${PKG_LIBNGHTTP3:-not-run}"
    print_kv "pkg_config_openssl" "${PKG_OPENSSL:-not-run}"
    print_kv "submodule_update_exit" "${SUBMODULE_UPDATE_EXIT:-not-run}"
    print_kv "cmake_configure_exit" "${CMAKE_CONFIGURE_EXIT:-not-run}"
    print_kv "cmake_build_exit" "${CMAKE_BUILD_EXIT:-not-run}"
    print_kv "example_binaries_present" "${EXAMPLE_BINARIES_PRESENT:-not-run}"
    print_kv "openssl_cert_exit" "${OPENSSL_CERT_EXIT:-not-run}"
    print_kv "server_pid" "${SERVER_PID:-not-run}"
    print_kv "client_exit" "${CLIENT_EXIT:-not-run}"
    print_kv "client_timeout_seconds" "$CLIENT_TIMEOUT_SECONDS"
    print_kv "client_local_addr_change_count" "${CLIENT_LOCAL_ADDR_CHANGE_COUNT:-not-run}"
    print_kv "client_immediate_migration_error_count" "${CLIENT_IMMEDIATE_MIGRATION_ERROR_COUNT:-not-run}"
    print_kv "client_qlog_count" "${CLIENT_QLOG_COUNT:-not-run}"
    print_kv "server_qlog_count" "${SERVER_QLOG_COUNT:-not-run}"
    print_kv "path_challenge_count" "${PATH_CHALLENGE_COUNT:-not-run}"
    print_kv "path_response_count" "${PATH_RESPONSE_COUNT:-not-run}"
    print_kv "validation" "$validation"
    print_kv "blocked_or_failed_reason" "$reason"
    print_kv "stage" "$stage"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# ngtcp2 Example Migration Demo Artifact

This artifact is public-safe. It records a fail-closed ngtcp2 example client/server migration gate without storing credentials, private keys, keylogs, pcaps, NetLogs, hostnames, account identifiers, or raw qlog contents in the tracked report.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| ngtcp2 dir | \`$NGTCP2_DIR\` |
| observed commit | \`${NGTCP2_OBSERVED_COMMIT:-not-observed}\` |
| expected commit | \`$NGTCP2_EXPECTED_COMMIT\` |
| commit matches | \`${NGTCP2_COMMIT_MATCHES:-unknown}\` |
| validation | \`$validation\` |
| reason | \`$reason\` |
| stage | \`$stage\` |

Do not convert a blocked artifact into a runtime PASS or FAIL claim. A paper-ready PASS requires the example binaries to build, the client to exit 0, the app response to complete, and migration/path-validation evidence to appear in logs or qlog-derived counters.
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

run_client_with_timeout() {
  python3 - "$CLIENT_TIMEOUT_SECONDS" "$@" >"$LOG_DIR/client.stdout" 2>"$LOG_DIR/client.stderr" <<'PY'
import subprocess
import sys

timeout = float(sys.argv[1])
cmd = sys.argv[2:]
try:
    proc = subprocess.run(cmd, timeout=timeout, check=False)
except subprocess.TimeoutExpired:
    raise SystemExit(124)
raise SystemExit(proc.returncode)
PY
}

if [[ ! -d "$NGTCP2_DIR" ]]; then
  fail_or_block "blocked" "missing_ngtcp2_source_dir" "preflight"
fi

NGTCP2_OBSERVED_COMMIT="$(git -C "$NGTCP2_DIR" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "$NGTCP2_OBSERVED_COMMIT" == "$NGTCP2_EXPECTED_COMMIT" ]]; then
  NGTCP2_COMMIT_MATCHES="yes"
else
  NGTCP2_COMMIT_MATCHES="no"
fi

if [[ "$NGTCP2_COMMIT_MATCHES" != "yes" && "$ALLOW_COMMIT_MISMATCH" != "1" ]]; then
  fail_or_block "blocked" "ngtcp2_commit_mismatch" "preflight"
fi

detect_libev_fallback

MISSING=()
for command_name in git cmake pkg-config openssl python3 cc c++; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    MISSING+=("$command_name")
  fi
done
if [[ "$CMAKE_GENERATOR" == "Ninja" ]] && ! command -v ninja >/dev/null 2>&1; then
  MISSING+=("ninja")
fi
if [[ "${#MISSING[@]}" -gt 0 ]]; then
  PREFLIGHT_MISSING_COMMANDS="$(IFS=,; echo "${MISSING[*]}")"
  fail_or_block "blocked" "missing_required_commands" "preflight"
fi
PREFLIGHT_MISSING_COMMANDS="none"

PKG_LIBEV="$(pkg_version libev)"
PKG_LIBNGHTTP3="$(pkg_version libnghttp3)"
PKG_OPENSSL="$(pkg_version openssl)"

if [[ "$PKG_LIBEV" == "missing" ]]; then
  fail_or_block "blocked" "missing_pkg_config_libev" "preflight"
fi
if [[ "$PKG_LIBNGHTTP3" == "missing" ]]; then
  fail_or_block "blocked" "missing_pkg_config_libnghttp3" "preflight"
fi
if [[ "$PKG_OPENSSL" == "missing" ]]; then
  fail_or_block "blocked" "missing_pkg_config_openssl" "preflight"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  write_result "blocked" "dry_run_only" "preflight"
  exit 0
fi

if [[ "$UPDATE_SUBMODULES" == "1" ]]; then
  set +e
  git -C "$NGTCP2_DIR" submodule update --init --recursive \
    >"$LOG_DIR/submodule-update.stdout" \
    2>"$LOG_DIR/submodule-update.stderr"
  SUBMODULE_UPDATE_EXIT=$?
  set -e
  if [[ "$SUBMODULE_UPDATE_EXIT" != "0" ]]; then
    fail_or_block "failed" "submodule_update_failed" "submodule_update"
  fi
fi

set +e
CMAKE_LIBEV_ARGS=()
if [[ -n "$LIBEV_INCLUDE_DIR" && -n "$LIBEV_LIBRARY" ]]; then
  CMAKE_LIBEV_ARGS=(
    "-DLIBEV_INCLUDE_DIR=$LIBEV_INCLUDE_DIR"
    "-DLIBEV_LIBRARY=$LIBEV_LIBRARY"
  )
fi

cmake -S "$NGTCP2_DIR" -B "$BUILD_DIR" -G "$CMAKE_GENERATOR" \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DENABLE_LIB_ONLY=OFF \
  -DBUILD_TESTING=ON \
  "${CMAKE_LIBEV_ARGS[@]}" \
  >"$LOG_DIR/cmake-configure.stdout" \
  2>"$LOG_DIR/cmake-configure.stderr"
CMAKE_CONFIGURE_EXIT=$?
set -e

if [[ "$CMAKE_CONFIGURE_EXIT" != "0" ]]; then
  fail_or_block "failed" "cmake_configure_failed" "cmake_configure"
fi

set +e
cmake --build "$BUILD_DIR" --target osslclient osslserver -j "$JOBS" \
  >"$LOG_DIR/cmake-build.stdout" \
  2>"$LOG_DIR/cmake-build.stderr"
CMAKE_BUILD_EXIT=$?
set -e

if [[ "$CMAKE_BUILD_EXIT" != "0" ]]; then
  fail_or_block "failed" "cmake_build_failed" "cmake_build"
fi

CLIENT_BIN="$BUILD_DIR/examples/osslclient"
SERVER_BIN="$BUILD_DIR/examples/osslserver"
if [[ -x "$CLIENT_BIN" && -x "$SERVER_BIN" ]]; then
  EXAMPLE_BINARIES_PRESENT="yes"
else
  EXAMPLE_BINARIES_PRESENT="no"
  fail_or_block "failed" "example_binaries_missing" "cmake_build"
fi

PRIVATE_DIR="$ARTIFACT_DIR/private"
HTDOCS_DIR="$ARTIFACT_DIR/htdocs"
CLIENT_QLOG_DIR="$ARTIFACT_DIR/qlog/client"
SERVER_QLOG_DIR="$ARTIFACT_DIR/qlog/server"
rm -rf "$PRIVATE_DIR" "$HTDOCS_DIR" "$ARTIFACT_DIR/qlog"
mkdir -p "$PRIVATE_DIR" "$HTDOCS_DIR" "$CLIENT_QLOG_DIR" "$SERVER_QLOG_DIR"
printf 'ngtcp2 example migration demo\n' >"$HTDOCS_DIR/index.txt"
python3 - "$HTDOCS_DIR/payload.bin" "$PAYLOAD_SIZE_BYTES" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
size = int(sys.argv[2])
chunk = (b"ngtcp2-migration-payload\n" * 4096)
remaining = size
with path.open("wb") as fp:
    while remaining > 0:
        data = chunk[: min(len(chunk), remaining)]
        fp.write(data)
        remaining -= len(data)
PY

set +e
openssl req -newkey rsa:2048 -x509 -nodes \
  -keyout "$PRIVATE_DIR/server.key" \
  -new \
  -out "$PRIVATE_DIR/server.crt" \
  -subj /CN=localhost \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
  >"$LOG_DIR/openssl-cert.stdout" \
  2>"$LOG_DIR/openssl-cert.stderr"
OPENSSL_CERT_EXIT=$?
set -e
if [[ "$OPENSSL_CERT_EXIT" != "0" ]]; then
  fail_or_block "failed" "openssl_cert_failed" "certificate"
fi

"$SERVER_BIN" \
  --qlog-dir="$SERVER_QLOG_DIR" \
  --htdocs="$HTDOCS_DIR" \
  127.0.0.1 "$PORT" "$PRIVATE_DIR/server.key" "$PRIVATE_DIR/server.crt" \
  >"$LOG_DIR/server.stdout" \
  2>"$LOG_DIR/server.stderr" &
SERVER_PID=$!
sleep "$SERVER_STARTUP_SECONDS"

if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
  fail_or_block "failed" "server_exited_before_client" "server_start"
fi

CLIENT_ARGS=(
  "$CLIENT_BIN"
  "--qlog-dir=$CLIENT_QLOG_DIR"
  "--change-local-addr=$CHANGE_LOCAL_ADDR_AFTER"
  "--exit-on-all-streams-close"
  "--no-http-dump"
)
if [[ -n "$CLIENT_EXTRA_ARGS" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=($CLIENT_EXTRA_ARGS)
  CLIENT_ARGS+=("${EXTRA_ARGS[@]}")
fi
CLIENT_ARGS+=(127.0.0.1 "$PORT" "https://localhost:$PORT/payload.bin")

set +e
export SSL_CERT_FILE="$PRIVATE_DIR/server.crt"
run_client_with_timeout "${CLIENT_ARGS[@]}"
CLIENT_EXIT=$?
unset SSL_CERT_FILE
set -e

cleanup
SERVER_PID=""

CLIENT_LOCAL_ADDR_CHANGE_COUNT="$(count_text "Local address is now" "$LOG_DIR/client.stderr" "$LOG_DIR/client.stdout")"
CLIENT_IMMEDIATE_MIGRATION_ERROR_COUNT="$(count_text "ngtcp2_conn_initiate_immediate_migration" "$LOG_DIR/client.stderr" "$LOG_DIR/client.stdout")"
CLIENT_QLOG_COUNT="$(find "$CLIENT_QLOG_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')"
SERVER_QLOG_COUNT="$(find "$SERVER_QLOG_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')"
PATH_CHALLENGE_COUNT="$(count_text "PATH_CHALLENGE|path_challenge" "$CLIENT_QLOG_DIR" "$SERVER_QLOG_DIR" "$LOG_DIR/client.stderr" "$LOG_DIR/server.stderr")"
PATH_RESPONSE_COUNT="$(count_text "PATH_RESPONSE|path_response" "$CLIENT_QLOG_DIR" "$SERVER_QLOG_DIR" "$LOG_DIR/client.stderr" "$LOG_DIR/server.stderr")"

if [[ "$CLIENT_EXIT" == "0" && "$CLIENT_LOCAL_ADDR_CHANGE_COUNT" != "0" && "$PATH_CHALLENGE_COUNT" != "0" && "$PATH_RESPONSE_COUNT" != "0" ]]; then
  write_result "ok" "none" "client"
  exit 0
fi

if [[ "$CLIENT_EXIT" == "0" ]]; then
  fail_or_block "failed" "client_completed_without_migration_frame_evidence" "client"
fi

fail_or_block "failed" "client_failed_or_timed_out" "client"
