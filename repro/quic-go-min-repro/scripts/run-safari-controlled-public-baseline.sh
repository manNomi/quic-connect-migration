#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$REPRO_DIR/../.." && pwd)"
cd "$REPRO_DIR"

RUN_ID="${RUN_ID:-safari-controlled-public-h3-baseline-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_URL:?set PUBLIC_ORIGIN_URL, e.g. https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=safari-public-slow}"
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="${CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR:-$ARTIFACT_DIR}"
RUN_SAFARI_CLASSIFIER="${RUN_SAFARI_CLASSIFIER:-auto}"
REQUIRE_SAFARI_APPLICATION_H3="${REQUIRE_SAFARI_APPLICATION_H3:-0}"
REQUIRE_H3_ALT_SVC="${REQUIRE_H3_ALT_SVC:-1}"
SAFARI_PORT="${SAFARI_PORT:-4444}"
SAFARI_WAIT_SECONDS="${SAFARI_WAIT_SECONDS:-8}"
MIN_ARTIFACT_FREE_GIB="${MIN_ARTIFACT_FREE_GIB:-7}"

"$SCRIPT_DIR/ensure-min-disk-free.sh" "$MIN_ARTIFACT_FREE_GIB" "$REPRO_DIR"

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

if ! command -v safaridriver >/dev/null 2>&1; then
  echo "safaridriver not found" >&2
  exit 2
fi

READINESS_ARGS=(--url "$PUBLIC_ORIGIN_URL" --format json)
if [[ "$REQUIRE_H3_ALT_SVC" == "1" ]]; then
  READINESS_ARGS+=(--require-h3-alt-svc)
fi
python3 "$PROJECT_ROOT/tools/check_public_origin_readiness.py" "${READINESS_ARGS[@]}" \
  >"$ARTIFACT_DIR/results/public-origin-readiness.json"

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --output "$ARTIFACT_DIR/results/client-path-before.json" || true

SAFARI_EXIT=0
python3 "$PROJECT_ROOT/tools/run_safari_webdriver_navigation.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --port "$SAFARI_PORT" \
  --wait-seconds "$SAFARI_WAIT_SECONDS" \
  --safaridriver-log "$ARTIFACT_DIR/logs/safaridriver.log" \
  --output "$ARTIFACT_DIR/results/safari-navigation.json" || SAFARI_EXIT=$?

python3 "$PROJECT_ROOT/tools/capture_network_path_snapshot.py" \
  --url "$PUBLIC_ORIGIN_URL" \
  --output "$ARTIFACT_DIR/results/client-path-after.json" || true

if [[ -f "$ARTIFACT_DIR/results/client-path-before.json" && -f "$ARTIFACT_DIR/results/client-path-after.json" ]]; then
  python3 "$PROJECT_ROOT/tools/compare_network_path_snapshots.py" \
    "$ARTIFACT_DIR/results/client-path-before.json" \
    "$ARTIFACT_DIR/results/client-path-after.json" \
    --output "$ARTIFACT_DIR/results/client-path-change-summary.json" || true
fi

if [[ "$RUN_SAFARI_CLASSIFIER" == "1" || ( "$RUN_SAFARI_CLASSIFIER" == "auto" && -f "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR/results/server.json" ) ]]; then
  SAFARI_SUMMARY="$ARTIFACT_DIR/results/safari-controlled-public-h3-baseline-summary.json"
  CLASSIFIER_ARGS=(
    "$ARTIFACT_DIR"
    --server-artifact-dir "$CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR"
    --browser-artifact-dir "$ARTIFACT_DIR"
    --url "$PUBLIC_ORIGIN_URL"
    --allow-missing-browser-summary
    --output "$SAFARI_SUMMARY"
  )
  if [[ -n "${CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}" ]]; then
    CLASSIFIER_ARGS+=(--expected-requests "$CONTROLLED_PUBLIC_EXPECTED_REQUESTS")
  fi
  python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_baseline.py" "${CLASSIFIER_ARGS[@]}"
  if [[ "$REQUIRE_SAFARI_APPLICATION_H3" == "1" ]]; then
    python3 - "$SAFARI_SUMMARY" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1], encoding="utf-8"))
if summary.get("status") not in ("PASS", "PASS_FEASIBILITY"):
    raise SystemExit(f"Safari controlled public H3 gate did not pass: {summary.get('status')} / {summary.get('classification')}")
PY
  fi
fi

exit "$SAFARI_EXIT"
