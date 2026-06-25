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
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-$ARTIFACT_DIR}"
RUN_CONTROLLED_PUBLIC_CLASSIFIER="${RUN_CONTROLLED_PUBLIC_CLASSIFIER:-auto}"
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3="${REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3:-0}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-7}"

"$SCRIPT_DIR/ensure-min-disk-free.sh" "$MIN_ARTIFACT_FREE_GIB" "$REPRO_DIR"

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

if [[ "$RUN_CONTROLLED_PUBLIC_CLASSIFIER" == "1" || ( "$RUN_CONTROLLED_PUBLIC_CLASSIFIER" == "auto" && -f "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR/results/server.json" ) ]]; then
  CONTROLLED_PUBLIC_SUMMARY="$ARTIFACT_DIR/results/controlled-public-h3-baseline-summary.json"
  CLASSIFIER_ARGS=(
    "$ARTIFACT_DIR"
    --server-artifact-dir "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR"
    --browser-artifact-dir "$ARTIFACT_DIR"
    --url "$SECOND_URL"
    --output "$CONTROLLED_PUBLIC_SUMMARY"
  )
  if [[ -n "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" ]]; then
    CLASSIFIER_ARGS+=(--expected-requests "$CONTROLLED_PUBLIC_EXPECTED_REQUESTS")
  fi
  python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_baseline.py" "${CLASSIFIER_ARGS[@]}"
  if [[ "$REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3" == "1" ]]; then
    python3 - "$CONTROLLED_PUBLIC_SUMMARY" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1], encoding="utf-8"))
if summary.get("status") != "PASS":
    raise SystemExit(f"controlled public application H3 gate did not PASS: {summary.get('status')} / {summary.get('classification')}")
PY
  fi
fi
