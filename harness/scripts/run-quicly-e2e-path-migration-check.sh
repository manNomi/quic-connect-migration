#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

QUICLY_DIR="${QUICLY_DIR:-/private/tmp/quic-cm-scan-repos/quicly}"
QUICLY_BUILD_DIR="${QUICLY_BUILD_DIR:-$QUICLY_DIR/build-local}"
RUN_ID="${RUN_ID:-quicly-e2e-path-migration-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
RESULT_DIR="$ARTIFACT_DIR/results"
LOG_DIR="$ARTIFACT_DIR/logs"
REQUIRE_FULL_E2E="${REQUIRE_FULL_E2E:-0}"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

CLI="$QUICLY_BUILD_DIR/cli"
UDPFW="$QUICLY_BUILD_DIR/udpfw"
E2E_T="$QUICLY_DIR/t/e2e.t"

BLOCKED_REASON="none"
READY="yes"
if [[ ! -d "$QUICLY_DIR" ]]; then
  READY="no"
  BLOCKED_REASON="missing_quicly_source"
elif [[ ! -x "$CLI" ]]; then
  READY="no"
  BLOCKED_REASON="missing_quicly_cli"
elif [[ ! -x "$UDPFW" ]]; then
  READY="no"
  BLOCKED_REASON="missing_quicly_udpfw"
elif [[ ! -f "$E2E_T" ]]; then
  READY="no"
  BLOCKED_REASON="missing_e2e_t"
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
if [[ -d "$QUICLY_DIR" ]]; then
  PERL_LIB_PATHS+=("$QUICLY_DIR")
fi
JOINED_PERL5LIB="$(IFS=:; echo "${PERL_LIB_PATHS[*]:-}")"

NET_EMPTY_PORT_READY="unknown"
if [[ "$READY" == "yes" ]]; then
  if env PERL5LIB="$JOINED_PERL5LIB" perl -MNet::EmptyPort -e 'print "ok\n"' >"$LOG_DIR/perl-net-empty-port-check.txt" 2>&1; then
    NET_EMPTY_PORT_READY="yes"
  else
    NET_EMPTY_PORT_READY="no"
    READY="no"
    BLOCKED_REASON="missing_perl_net_empty_port"
  fi
fi

if [[ "$READY" != "yes" ]]; then
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$ARTIFACT_DIR"
    print_kv "quicly_dir" "$QUICLY_DIR"
    print_kv "quicly_build_dir" "$QUICLY_BUILD_DIR"
    print_kv "ready" "$READY"
    print_kv "blocked_reason" "$BLOCKED_REASON"
    print_kv "net_empty_port_ready" "$NET_EMPTY_PORT_READY"
    print_kv "validation" "blocked"
  } | tee "$RESULT_DIR/result.env"
  exit 0
fi

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

VALIDATION="failed"
if [[ "$PATH_SUBTEST_OK" == "yes" ]]; then
  VALIDATION="ok_path_migration"
fi
if [[ "$REQUIRE_FULL_E2E" == "1" && "$PROVE_EXIT" != "0" ]]; then
  VALIDATION="failed_full_e2e"
fi

{
  print_kv "run_id" "$RUN_ID"
  print_kv "artifact_dir" "$ARTIFACT_DIR"
  print_kv "quicly_dir" "$QUICLY_DIR"
  print_kv "quicly_build_dir" "$QUICLY_BUILD_DIR"
  print_kv "ready" "$READY"
  print_kv "blocked_reason" "$BLOCKED_REASON"
  print_kv "net_empty_port_ready" "$NET_EMPTY_PORT_READY"
  print_kv "prove_exit" "$PROVE_EXIT"
  print_kv "path_subtest_seen" "$PATH_SUBTEST_SEEN"
  print_kv "path_subtest_ok" "$PATH_SUBTEST_OK"
  print_kv "cid_seq_check_ok" "$CID_SEQ_CHECK_OK"
  print_kv "slow_start_failed" "$SLOW_START_FAILED"
  print_kv "result_fail" "$RESULT_FAIL"
  print_kv "validation" "$VALIDATION"
} | tee "$RESULT_DIR/result.env"

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
end = min(len(lines), start + 90)
out_path.write_text("\n".join(f"{i + 1}: {lines[i]}" for i in range(start, end)) + "\n")
PY

cat >"$RESULT_DIR/README.md" <<EOF
# quicly e2e path-migration artifact

This artifact intentionally separates the quicly \`path-migration\` e2e subtest from the full \`t/e2e.t\` result.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| prove exit | \`$PROVE_EXIT\` |
| path subtest ok | \`$PATH_SUBTEST_OK\` |
| CID seq check ok | \`$CID_SEQ_CHECK_OK\` |
| slow-start failed | \`$SLOW_START_FAILED\` |
| validation | \`$VALIDATION\` |

Use \`results/path-migration-excerpt.txt\` for the public-safe TAP excerpt and \`logs/prove-e2e.log\` for the local raw log.
EOF

if [[ "$VALIDATION" == "failed" || "$VALIDATION" == "failed_full_e2e" ]]; then
  exit 1
fi
