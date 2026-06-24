#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

MATRIX_ID="${MATRIX_ID:-quic-go-h3-midflight-matrix-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/${MATRIX_ID}}"
REPEAT_COUNT="${REPEAT_COUNT:-3}"
BASE_PORT="${BASE_PORT:-4800}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
MIGRATION_AT_BYTES="${MIGRATION_AT_BYTES:-524288}"
CHUNK_BYTES="${CHUNK_BYTES:-16384}"
CHUNK_DELAY="${CHUNK_DELAY:-2ms}"
TIMEOUT="${TIMEOUT:-45s}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-5s}"

mkdir -p "$ARTIFACT_ROOT/results"

artifact_dirs=()
for ((rep = 1; rep <= REPEAT_COUNT; rep += 1)); do
  upload_port=$((BASE_PORT + ((rep - 1) * 2)))
  download_port=$((upload_port + 1))
  run_id="${MATRIX_ID}-r${rep}"
  artifact_dir="${ARTIFACT_ROOT}/r${rep}"
  artifact_dirs+=("$artifact_dir")

  RUN_ID="$run_id" \
    ARTIFACT_DIR="$artifact_dir" \
    UPLOAD_ADDR="127.0.0.1:${upload_port}" \
    DOWNLOAD_ADDR="127.0.0.1:${download_port}" \
    PAYLOAD_BYTES="$PAYLOAD_BYTES" \
    MIGRATION_AT_BYTES="$MIGRATION_AT_BYTES" \
    CHUNK_BYTES="$CHUNK_BYTES" \
    CHUNK_DELAY="$CHUNK_DELAY" \
    TIMEOUT="$TIMEOUT" \
    PROBE_TIMEOUT="$PROBE_TIMEOUT" \
    ./scripts/run-local-h3-midflight.sh
done

python3 "$PROJECT_ROOT/tools/summarize_quic_go_h3_midflight_matrix.py" "${artifact_dirs[@]}" \
  --output "$ARTIFACT_ROOT/results/matrix-summary.md" \
  --csv-output "$ARTIFACT_ROOT/results/matrix-summary.csv"
