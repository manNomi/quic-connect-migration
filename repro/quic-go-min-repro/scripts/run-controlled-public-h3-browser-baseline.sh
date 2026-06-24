#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

RUN_ID="${RUN_ID:-controlled-public-h3-browser-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:?set PUBLIC_ORIGIN_URL, e.g. https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow}"
SECOND_URL="${SECOND_URL:-$PUBLIC_ORIGIN_URL}"
REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}"

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

READINESS_ARGS=(--url "$PUBLIC_ORIGIN_URL" --format json)
if [[ "$REQUIRE_H3_ALT_SVC" == "1" ]]; then
  READINESS_ARGS+=(--require-h3-alt-svc)
fi

python3 "$PROJECT_ROOT/tools/check_public_origin_readiness.py" "${READINESS_ARGS[@]}" \
  >"$ARTIFACT_DIR/results/public-origin-readiness.json"

TARGET_URL="$PUBLIC_ORIGIN_URL" \
SECOND_URL="$SECOND_URL" \
ARTIFACT_DIR="$ARTIFACT_DIR" \
RUN_ID="$RUN_ID" \
./scripts/run-chrome-public-h3.sh
