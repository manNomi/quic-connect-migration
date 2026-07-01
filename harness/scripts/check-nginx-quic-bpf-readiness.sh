#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

NGINX_DIR="${NGINX_DIR:-/private/tmp/quic-cm-scan-repos/nginx}"
NGINX_BIN="${NGINX_BIN:-${NGINX_BUILD_DIR:-$NGINX_DIR/build-quic-runtime}/nginx}"
RUN_ID="${RUN_ID:-nginx-quic-bpf-readiness-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"
REQUIRE_READY="${REQUIRE_READY:-0}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

bool_text() {
  if "$@"; then
    printf 'yes'
  else
    printf 'no'
  fi
}

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
if [[ "$SYSTEM_NAME" == "Linux" ]]; then
  LINUX_READY="yes"
fi

ROOT_READY="no"
if [[ "$(id -u)" == "0" ]]; then
  ROOT_READY="yes"
fi

SYS_FS_BPF_READY="no"
if [[ -d /sys/fs/bpf && -w /sys/fs/bpf ]]; then
  SYS_FS_BPF_READY="yes"
fi

SOURCE_READY="no"
if [[ -d "$NGINX_DIR" ]]; then
  SOURCE_READY="yes"
fi

SOURCE_HAS_QUIC_BPF="no"
SOURCE_HAS_MIGRATION="no"
if [[ "$SOURCE_READY" == "yes" ]]; then
  if file_contains "quic_bpf|NGX_HTTP_V3_H" "$NGINX_DIR/src" "$NGINX_DIR/docs" "$NGINX_DIR/conf" "$NGINX_DIR/auto"; then
    SOURCE_HAS_QUIC_BPF="yes"
  fi
  if [[ -f "$NGINX_DIR/src/event/quic/ngx_event_quic_migration.c" ]]; then
    SOURCE_HAS_MIGRATION="yes"
  fi
fi

RUNTIME_DEMO_READY="no"
if [[ -x "$SCRIPT_DIR/run-nginx-quic-active-migration-demo.sh" ]]; then
  RUNTIME_DEMO_READY="yes"
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

CAN_RUN_LINUX_QUIC_BPF_NOW="yes"
BLOCKED_REASON="none"
if [[ "$SOURCE_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="missing_nginx_source"
elif [[ "$SOURCE_HAS_QUIC_BPF" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="source_quic_bpf_not_found"
elif [[ "$LINUX_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="linux_required"
elif [[ "$ROOT_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="root_or_capability_required"
elif [[ "$SYS_FS_BPF_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="missing_writable_sys_fs_bpf"
elif [[ "$NGINX_BIN_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="missing_nginx_binary"
elif [[ "$NGINX_V3_MODULE_READY" != "yes" ]]; then
  CAN_RUN_LINUX_QUIC_BPF_NOW="no"
  BLOCKED_REASON="nginx_without_http_v3_module"
fi

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
  print_kv "runtime_demo_script_ready" "$RUNTIME_DEMO_READY"
  print_kv "linux_ready" "$LINUX_READY"
  print_kv "root_ready" "$ROOT_READY"
  print_kv "sys_fs_bpf_ready" "$SYS_FS_BPF_READY"
  print_kv "nginx_bin_ready" "$NGINX_BIN_READY"
  print_kv "nginx_v3_module_ready" "$NGINX_V3_MODULE_READY"
  print_kv "nginx_version_exit" "$VERSION_EXIT"
  print_kv "can_run_linux_quic_bpf_now" "$CAN_RUN_LINUX_QUIC_BPF_NOW"
  print_kv "blocked_reason" "$BLOCKED_REASON"
} | tee "$RESULT_DIR/result.env"

cat >"$RESULT_DIR/README.md" <<EOF
# nginx quic_bpf Readiness Artifact

This artifact is public-safe. It separates the already completed local nginx HTTP/3 active-migration runtime demo from a future Linux/eBPF production-routing check.

## Summary

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| source ready | \`$SOURCE_READY\` |
| source has quic_bpf | \`$SOURCE_HAS_QUIC_BPF\` |
| source has migration file | \`$SOURCE_HAS_MIGRATION\` |
| runtime demo script ready | \`$RUNTIME_DEMO_READY\` |
| Linux ready | \`$LINUX_READY\` |
| root ready | \`$ROOT_READY\` |
| /sys/fs/bpf ready | \`$SYS_FS_BPF_READY\` |
| nginx binary ready | \`$NGINX_BIN_READY\` |
| nginx HTTP/3 module ready | \`$NGINX_V3_MODULE_READY\` |
| can run Linux quic_bpf now | \`$CAN_RUN_LINUX_QUIC_BPF_NOW\` |
| blocked reason | \`$BLOCKED_REASON\` |

## Interpretation

- The local nginx runtime demo is evidence that nginx can handle a quiche active source-port migration on loopback.
- A Linux \`quic_bpf\` check is a different deployment claim involving packet routing support and host capabilities.
- If this readiness artifact is blocked on macOS, do not interpret that as nginx QUIC migration failure.
EOF

if [[ "$REQUIRE_READY" == "1" && "$CAN_RUN_LINUX_QUIC_BPF_NOW" != "yes" ]]; then
  exit 1
fi
