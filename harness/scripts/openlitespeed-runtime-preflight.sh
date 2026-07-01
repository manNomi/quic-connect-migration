#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

OPENLITESPEED_DIR="${OPENLITESPEED_DIR:-/private/tmp/quic-cm-scan-repos/openlitespeed}"
LSQUIC_DIR="${LSQUIC_DIR:-/private/tmp/quic-cm-scan-repos/lsquic}"
QUICHE_CLIENT="${QUICHE_CLIENT:-/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client}"
MIN_DISK_GIB="${MIN_DISK_GIB:-30}"
RUN_ID="${RUN_ID:-openlitespeed-runtime-preflight-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
REQUIRE_READY="${REQUIRE_READY:-0}"

mkdir -p "$ARTIFACT_DIR"

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

bool_text() {
  if [[ "$1" == "1" ]]; then
    printf 'yes'
  else
    printf 'no'
  fi
}

check_executable() {
  local path="$1"
  [[ -n "$path" && -x "$path" ]]
}

free_gib() {
  python3 - <<'PY'
import shutil
print(round(shutil.disk_usage(".").free / (1024 ** 3), 2))
PY
}

gte_float() {
  python3 - "$1" "$2" <<'PY'
import sys
actual = float(sys.argv[1])
minimum = float(sys.argv[2])
raise SystemExit(0 if actual >= minimum else 1)
PY
}

git_value() {
  local repo="$1"
  shift
  if [[ -d "$repo/.git" ]]; then
    git -C "$repo" "$@" 2>/dev/null || true
  fi
}

count_pattern() {
  local pattern="$1"
  shift
  if have_cmd rg; then
    (rg --no-ignore --text "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
  else
    (grep -R -E "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
  fi
}

SYSTEM_NAME="$(uname -s)"
SYSTEM_MACHINE="$(uname -m)"
DISK_FREE_GIB="$(free_gib)"

SOURCE_READY=0
if [[ -d "$OPENLITESPEED_DIR/.git" ]]; then
  SOURCE_READY=1
fi

OLS_COMMIT="$(git_value "$OPENLITESPEED_DIR" rev-parse HEAD)"
OLS_DATE="$(git_value "$OPENLITESPEED_DIR" show -s --format=%cI HEAD)"
OLS_SUBJECT="$(git_value "$OPENLITESPEED_DIR" show -s --format=%s HEAD)"

LSQUIC_POINTER=""
if [[ -f "$OPENLITESPEED_DIR/LSQUICCOMMIT" ]]; then
  LSQUIC_POINTER="$(tr -d '[:space:]' <"$OPENLITESPEED_DIR/LSQUICCOMMIT")"
fi

LOCAL_LSQUIC_COMMIT="$(git_value "$LSQUIC_DIR" rev-parse HEAD)"

LSQUIC_POINTER_READY=0
if [[ -n "$LSQUIC_POINTER" ]]; then
  LSQUIC_POINTER_READY=1
fi

LOCAL_LSQUIC_MATCH=0
if [[ -n "$LSQUIC_POINTER" && "$LSQUIC_POINTER" == "$LOCAL_LSQUIC_COMMIT" ]]; then
  LOCAL_LSQUIC_MATCH=1
fi

SUBMODULE_READY=0
if [[ -d "$OPENLITESPEED_DIR/src/liblsquic" ]]; then
  SUBMODULE_READY=1
fi

DEV_SHM_READY=0
if [[ -d /dev/shm && -w /dev/shm ]]; then
  DEV_SHM_READY=1
fi

LINUX_READY=0
if [[ "$SYSTEM_NAME" == "Linux" ]]; then
  LINUX_READY=1
fi

DISK_READY=0
if gte_float "$DISK_FREE_GIB" "$MIN_DISK_GIB"; then
  DISK_READY=1
fi

CMAKE_READY=0
MAKE_READY=0
CC_READY=0
if have_cmd cmake; then CMAKE_READY=1; fi
if have_cmd make; then MAKE_READY=1; fi
if have_cmd cc || have_cmd clang || have_cmd gcc; then CC_READY=1; fi

BUILD_TOOLS_READY=0
if [[ "$CMAKE_READY" == "1" && "$MAKE_READY" == "1" && "$CC_READY" == "1" ]]; then
  BUILD_TOOLS_READY=1
fi

LSHTTPD_BIN="$(command -v lshttpd 2>/dev/null || true)"
OPENLITESPEED_BIN="$(command -v openlitespeed 2>/dev/null || true)"
BINARY_READY=0
if check_executable "$LSHTTPD_BIN" || check_executable "$OPENLITESPEED_BIN"; then
  BINARY_READY=1
fi

QUICHE_READY=0
if [[ -x "$QUICHE_CLIENT" ]]; then
  QUICHE_READY=1
fi

SOURCE_FEATURE_READY=0
if [[ "$SOURCE_READY" == "1" ]]; then
  if [[ -f "$OPENLITESPEED_DIR/CMakeLists.txt" \
        && -f "$OPENLITESPEED_DIR/dist/conf/httpd_config.conf.in" \
        && -f "$OPENLITESPEED_DIR/src/quic/quicengine.cpp" \
        && -f "$OPENLITESPEED_DIR/src/quic/udplistener.cpp" \
        && -f "$OPENLITESPEED_DIR/src/quic/quicshm.cpp" ]]; then
    SOURCE_FEATURE_READY=1
  fi
fi

LSENG_HTTP_SERVER_COUNT=0
QUIC_ENABLE_COUNT=0
SCID_CALLBACK_COUNT=0
CID_PID_COUNT=0
if [[ "$SOURCE_READY" == "1" ]]; then
  LSENG_HTTP_SERVER_COUNT="$(count_pattern "LSENG_HTTP_SERVER|lsquic_engine_new" "$OPENLITESPEED_DIR/src/quic/quicengine.cpp")"
  QUIC_ENABLE_COUNT="$(count_pattern "quicEnable|quicShmDir" "$OPENLITESPEED_DIR/dist/conf/httpd_config.conf.in")"
  SCID_CALLBACK_COUNT="$(count_pattern "ea_new_scids|ea_live_scids|ea_old_scids" "$OPENLITESPEED_DIR/src/quic/quicengine.cpp")"
  CID_PID_COUNT="$(count_pattern "lookupCidPid|lookupCidPids|m_pCidMap|CID/PID" "$OPENLITESPEED_DIR/src/quic/quicshm.cpp")"
fi

RUNTIME_READY=0
if [[ "$SOURCE_READY" == "1" \
      && "$LSQUIC_POINTER_READY" == "1" \
      && "$LOCAL_LSQUIC_MATCH" == "1" \
      && "$SUBMODULE_READY" == "1" \
      && "$BINARY_READY" == "1" \
      && "$QUICHE_READY" == "1" \
      && "$DEV_SHM_READY" == "1" \
      && "$DISK_READY" == "1" ]]; then
  RUNTIME_READY=1
fi

NEXT_ACTION="prepare-linux-or-cleanup-before-runtime-demo"
if [[ "$RUNTIME_READY" == "1" ]]; then
  NEXT_ACTION="run-openlitespeed-runtime-demo"
elif [[ "$DISK_READY" != "1" ]]; then
  NEXT_ACTION="free-disk-or-use-linux-ec2-before-openlitespeed-build"
elif [[ "$BINARY_READY" != "1" || "$SUBMODULE_READY" != "1" ]]; then
  NEXT_ACTION="install-or-build-openlitespeed-with-submodules"
fi

{
  print_kv run_id "$RUN_ID"
  print_kv artifact_dir "$ARTIFACT_DIR"
  print_kv openlitespeed_dir "$OPENLITESPEED_DIR"
  print_kv lsquic_dir "$LSQUIC_DIR"
  print_kv quiche_client "$QUICHE_CLIENT"
  print_kv system_name "$SYSTEM_NAME"
  print_kv system_machine "$SYSTEM_MACHINE"
  print_kv disk_free_gib "$DISK_FREE_GIB"
  print_kv min_disk_gib "$MIN_DISK_GIB"
  print_kv openlitespeed_commit "$OLS_COMMIT"
  print_kv openlitespeed_date "$OLS_DATE"
  print_kv openlitespeed_subject "$OLS_SUBJECT"
  print_kv lsquic_commit_pointer "$LSQUIC_POINTER"
  print_kv local_lsquic_commit "$LOCAL_LSQUIC_COMMIT"
  print_kv lshttpd_bin "$LSHTTPD_BIN"
  print_kv openlitespeed_bin "$OPENLITESPEED_BIN"
  print_kv source_ready "$(bool_text "$SOURCE_READY")"
  print_kv source_feature_ready "$(bool_text "$SOURCE_FEATURE_READY")"
  print_kv lsquic_pointer_ready "$(bool_text "$LSQUIC_POINTER_READY")"
  print_kv local_lsquic_match "$(bool_text "$LOCAL_LSQUIC_MATCH")"
  print_kv submodule_ready "$(bool_text "$SUBMODULE_READY")"
  print_kv binary_ready "$(bool_text "$BINARY_READY")"
  print_kv quiche_ready "$(bool_text "$QUICHE_READY")"
  print_kv build_tools_ready "$(bool_text "$BUILD_TOOLS_READY")"
  print_kv linux_recommended_ready "$(bool_text "$LINUX_READY")"
  print_kv dev_shm_ready "$(bool_text "$DEV_SHM_READY")"
  print_kv disk_ready "$(bool_text "$DISK_READY")"
  print_kv lseng_http_server_count "$LSENG_HTTP_SERVER_COUNT"
  print_kv quic_enable_count "$QUIC_ENABLE_COUNT"
  print_kv scid_callback_count "$SCID_CALLBACK_COUNT"
  print_kv cid_pid_count "$CID_PID_COUNT"
  print_kv runtime_ready "$(bool_text "$RUNTIME_READY")"
  print_kv next_action "$NEXT_ACTION"
} >"$ARTIFACT_DIR/result.env"

cat >"$ARTIFACT_DIR/report.md" <<EOF
# OpenLiteSpeed Runtime Preflight

Generated: \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`

## Summary

| item | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| runtime ready | \`$(bool_text "$RUNTIME_READY")\` |
| next action | \`$NEXT_ACTION\` |
| disk free GiB | \`$DISK_FREE_GIB\` |
| minimum disk GiB | \`$MIN_DISK_GIB\` |
| system | \`$SYSTEM_NAME $SYSTEM_MACHINE\` |

## Checks

| check | ok | evidence |
| --- | --- | --- |
| OpenLiteSpeed source clone | \`$(bool_text "$SOURCE_READY")\` | \`$OPENLITESPEED_DIR\` |
| Source feature files | \`$(bool_text "$SOURCE_FEATURE_READY")\` | CMake/config/src/quic files present |
| LSQUICCOMMIT present | \`$(bool_text "$LSQUIC_POINTER_READY")\` | \`$LSQUIC_POINTER\` |
| local LSQUIC matches pointer | \`$(bool_text "$LOCAL_LSQUIC_MATCH")\` | local \`$LOCAL_LSQUIC_COMMIT\` |
| OpenLiteSpeed submodule ready | \`$(bool_text "$SUBMODULE_READY")\` | \`$OPENLITESPEED_DIR/src/liblsquic\` |
| OpenLiteSpeed binary ready | \`$(bool_text "$BINARY_READY")\` | lshttpd=\`$LSHTTPD_BIN\`, openlitespeed=\`$OPENLITESPEED_BIN\` |
| quiche client ready | \`$(bool_text "$QUICHE_READY")\` | \`$QUICHE_CLIENT\` |
| build tools ready | \`$(bool_text "$BUILD_TOOLS_READY")\` | cmake=\`$(command -v cmake 2>/dev/null || true)\`, make=\`$(command -v make 2>/dev/null || true)\` |
| Linux recommended runtime | \`$(bool_text "$LINUX_READY")\` | \`$SYSTEM_NAME\` |
| /dev/shm ready | \`$(bool_text "$DEV_SHM_READY")\` | OpenLiteSpeed default quicShmDir uses /dev/shm |
| disk ready | \`$(bool_text "$DISK_READY")\` | \`$DISK_FREE_GIB >= $MIN_DISK_GIB\` |

## Source Pattern Counts

| pattern group | count |
| --- | ---: |
| LSENG_HTTP_SERVER / lsquic_engine_new | $LSENG_HTTP_SERVER_COUNT |
| quicEnable / quicShmDir | $QUIC_ENABLE_COUNT |
| SCID lifecycle callbacks | $SCID_CALLBACK_COUNT |
| CID/PID shared-memory mapping | $CID_PID_COUNT |

## Interpretation

This preflight is intentionally conservative. It does not build OpenLiteSpeed and does not claim runtime Connection Migration support. A runtime demo should only proceed after the binary/submodule, Linux or Linux-like shared-memory path, disk, and quiche client gates are ready.
EOF

cat "$ARTIFACT_DIR/result.env"

if [[ "$REQUIRE_READY" == "1" && "$RUNTIME_READY" != "1" ]]; then
  echo "openlitespeed_runtime_preflight=blocked" >&2
  exit 1
fi

if [[ "$RUNTIME_READY" == "1" ]]; then
  echo "openlitespeed_runtime_preflight=ready"
else
  echo "openlitespeed_runtime_preflight=blocked"
fi
