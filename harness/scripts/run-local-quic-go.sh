#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

require_command go

REPRO_DIR="$PROJECT_ROOT/experiments/quic-go-min-repro"
RUN_ID="${RUN_ID:-local-quic-go-$(timestamp_utc)}"
ARTIFACT_DIR="$HARNESS_DIR/results/$RUN_ID"

mkdir -p "$ARTIFACT_DIR/results"

export PORT="${PORT:-4242}"
export PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
export PROBE_TIMEOUT="${PROBE_TIMEOUT:-3s}"
export TIMEOUT="${TIMEOUT:-30s}"
export ARTIFACT_DIR

{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'experiment=direct-origin-local-quic-go\n'
  printf 'started_at=%s\n' "$(timestamp_utc)"
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'repro_dir=%s\n' "$REPRO_DIR"
  printf 'port=%s\n' "$PORT"
  printf 'payload_bytes=%s\n' "$PAYLOAD_BYTES"
  printf 'probe_timeout=%s\n' "$PROBE_TIMEOUT"
  printf 'timeout=%s\n' "$TIMEOUT"
} >"$ARTIFACT_DIR/results/manifest.env"

"$REPRO_DIR/scripts/run-local-happy-path.sh" | tee "$ARTIFACT_DIR/results/harness-run.log"

"$SCRIPT_DIR/validate-quic-go-artifacts.sh" "$ARTIFACT_DIR"

printf 'finished_at=%s\n' "$(timestamp_utc)" >>"$ARTIFACT_DIR/results/manifest.env"
printf 'status=ok\n' >>"$ARTIFACT_DIR/results/manifest.env"

echo
echo "local_quic_go=ok"
print_kv "run_id" "$RUN_ID"
print_kv "artifact_dir" "$ARTIFACT_DIR"
