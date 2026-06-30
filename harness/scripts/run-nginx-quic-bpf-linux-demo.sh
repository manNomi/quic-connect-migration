#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

RUN_ID="${RUN_ID:-nginx-quic-bpf-linux-demo-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"
REQUIRE_READY="${REQUIRE_READY:-0}"

NGINX_DIR="${NGINX_DIR:-/private/tmp/quic-cm-scan-repos/nginx}"
NGINX_BUILD_DIR="${NGINX_BUILD_DIR:-$NGINX_DIR/build-quic-runtime}"
NGINX_BIN="${NGINX_BIN:-$NGINX_BUILD_DIR/nginx}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

file_contains() {
  local pattern="$1"
  shift
  if command -v rg >/dev/null 2>&1; then
    rg --no-ignore --quiet -- "$pattern" "$@" 2>/dev/null
  else
    grep -R -q -E -- "$pattern" "$@" 2>/dev/null
  fi
}

SYSTEM_NAME="$(uname -s)"
SYSTEM_MACHINE="$(uname -m)"
LINUX_READY="no"
[[ "$SYSTEM_NAME" == "Linux" ]] && LINUX_READY="yes"

ROOT_READY="no"
[[ "$(id -u)" == "0" ]] && ROOT_READY="yes"

SYS_FS_BPF_READY="no"
if [[ -d /sys/fs/bpf && -w /sys/fs/bpf ]]; then
  SYS_FS_BPF_READY="yes"
fi

SOURCE_READY="no"
SOURCE_HAS_QUIC_BPF="no"
SOURCE_HAS_MIGRATION="no"
if [[ -d "$NGINX_DIR" ]]; then
  SOURCE_READY="yes"
  if file_contains "quic_bpf" "$NGINX_DIR/src" "$NGINX_DIR/conf" "$NGINX_DIR/docs" "$NGINX_DIR/contrib" 2>/dev/null; then
    SOURCE_HAS_QUIC_BPF="yes"
  fi
  if [[ -f "$NGINX_DIR/src/event/quic/ngx_event_quic_migration.c" ]]; then
    SOURCE_HAS_MIGRATION="yes"
  fi
fi

NGINX_BIN_READY="no"
NGINX_V3_MODULE_READY="unknown"
if [[ -x "$NGINX_BIN" ]]; then
  NGINX_BIN_READY="yes"
  set +e
  "$NGINX_BIN" -V >"$LOG_DIR/nginx-version.txt" 2>&1
  VERSION_EXIT=$?
  set -e
  if [[ "$VERSION_EXIT" == "0" ]] && file_contains "--with-http_v3_module" "$LOG_DIR/nginx-version.txt"; then
    NGINX_V3_MODULE_READY="yes"
  else
    NGINX_V3_MODULE_READY="no"
  fi
else
  VERSION_EXIT="not-run"
fi

ACTIVE_DEMO_READY="no"
if [[ -x "$SCRIPT_DIR/run-nginx-quic-active-migration-demo.sh" ]]; then
  ACTIVE_DEMO_READY="yes"
fi

CAN_RUN="yes"
BLOCKED_REASON="none"
if [[ "$SOURCE_READY" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="missing_nginx_source"
elif [[ "$SOURCE_HAS_QUIC_BPF" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="source_quic_bpf_not_found"
elif [[ "$SOURCE_HAS_MIGRATION" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="source_migration_file_missing"
elif [[ "$LINUX_READY" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="linux_required"
elif [[ "$ROOT_READY" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="root_or_capability_required"
elif [[ "$SYS_FS_BPF_READY" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="missing_writable_sys_fs_bpf"
elif [[ "$ACTIVE_DEMO_READY" != "yes" ]]; then
  CAN_RUN="no"
  BLOCKED_REASON="missing_active_migration_demo_runner"
fi

write_blocked_result() {
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "system_name" "$SYSTEM_NAME"
    print_kv "system_machine" "$SYSTEM_MACHINE"
    print_kv "nginx_dir" "$NGINX_DIR"
    print_kv "nginx_bin" "$NGINX_BIN"
    print_kv "source_ready" "$SOURCE_READY"
    print_kv "source_has_quic_bpf" "$SOURCE_HAS_QUIC_BPF"
    print_kv "source_has_migration_file" "$SOURCE_HAS_MIGRATION"
    print_kv "active_demo_runner_ready" "$ACTIVE_DEMO_READY"
    print_kv "linux_ready" "$LINUX_READY"
    print_kv "root_ready" "$ROOT_READY"
    print_kv "sys_fs_bpf_ready" "$SYS_FS_BPF_READY"
    print_kv "nginx_bin_ready" "$NGINX_BIN_READY"
    print_kv "nginx_v3_module_ready" "$NGINX_V3_MODULE_READY"
    print_kv "nginx_version_exit" "$VERSION_EXIT"
    print_kv "validation" "blocked"
    print_kv "blocked_reason" "$BLOCKED_REASON"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# nginx quic_bpf Linux Demo Artifact

This artifact is public-safe. The runner did not execute the active migration workload because a prerequisite gate was closed.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| system | \`$SYSTEM_NAME/$SYSTEM_MACHINE\` |
| source ready | \`$SOURCE_READY\` |
| source has quic_bpf | \`$SOURCE_HAS_QUIC_BPF\` |
| source has migration file | \`$SOURCE_HAS_MIGRATION\` |
| active demo runner ready | \`$ACTIVE_DEMO_READY\` |
| Linux ready | \`$LINUX_READY\` |
| root ready | \`$ROOT_READY\` |
| /sys/fs/bpf ready | \`$SYS_FS_BPF_READY\` |
| nginx binary ready | \`$NGINX_BIN_READY\` |
| nginx HTTP/3 module ready | \`$NGINX_V3_MODULE_READY\` |
| validation | \`blocked\` |
| blocked reason | \`$BLOCKED_REASON\` |

Do not treat this as a nginx QUIC migration failure. It is a deployment prerequisite result.
EOF
}

if [[ "$CAN_RUN" != "yes" ]]; then
  write_blocked_result
  if [[ "$REQUIRE_READY" == "1" ]]; then
    exit 1
  fi
  exit 0
fi

DEMO_RUN_ID="${RUN_ID}-active"
DEMO_ARTIFACT_DIR="$ARTIFACT_DIR/active-demo"

set +e
RUN_ID="$DEMO_RUN_ID" \
ARTIFACT_DIR="$DEMO_ARTIFACT_DIR" \
NGINX_QUIC_BPF=1 \
NGINX_DIR="$NGINX_DIR" \
NGINX_BUILD_DIR="$NGINX_BUILD_DIR" \
"$SCRIPT_DIR/run-nginx-quic-active-migration-demo.sh" \
  >"$LOG_DIR/active-demo.stdout" \
  2>"$LOG_DIR/active-demo.stderr"
DEMO_EXIT=$?
set -e

DEMO_VALIDATION="unknown"
if [[ -f "$DEMO_ARTIFACT_DIR/result.env" ]]; then
  # shellcheck disable=SC1090
  DEMO_VALIDATION="$(grep -E '^validation=' "$DEMO_ARTIFACT_DIR/result.env" | tail -n 1 | cut -d= -f2- || true)"
fi

{
  print_kv "run_id" "$RUN_ID"
  print_kv "artifact_dir" "$ARTIFACT_DIR"
  print_kv "system_name" "$SYSTEM_NAME"
  print_kv "system_machine" "$SYSTEM_MACHINE"
  print_kv "nginx_dir" "$NGINX_DIR"
  print_kv "nginx_bin" "$NGINX_BIN"
  print_kv "linux_ready" "$LINUX_READY"
  print_kv "root_ready" "$ROOT_READY"
  print_kv "sys_fs_bpf_ready" "$SYS_FS_BPF_READY"
  print_kv "nginx_quic_bpf" "1"
  print_kv "active_demo_artifact_dir" "$DEMO_ARTIFACT_DIR"
  print_kv "active_demo_exit" "$DEMO_EXIT"
  print_kv "active_demo_validation" "$DEMO_VALIDATION"
  if [[ "$DEMO_EXIT" == "0" && "$DEMO_VALIDATION" == "ok" ]]; then
    print_kv "validation" "ok"
  else
    print_kv "validation" "failed"
  fi
} | tee "$RESULT_DIR/result.env"

if [[ "$DEMO_EXIT" != "0" || "$DEMO_VALIDATION" != "ok" ]]; then
  exit 1
fi
