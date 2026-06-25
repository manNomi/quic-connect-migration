#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command python3

TEMPLATE_FILE="${CONTROLLED_PUBLIC_TEMPLATE:-$HARNESS_DIR/config/controlled-public-origin.env.example}"
CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
OVERWRITE="${OVERWRITE:-0}"
REQUIRE_BASELINE_READY="${REQUIRE_BASELINE_READY:-0}"
OUTPUT_DIR="${CONTROLLED_PUBLIC_CONFIG_INIT_OUTPUT_DIR:-$PROJECT_ROOT/repro/quic-go-min-repro/artifacts/controlled-public-config-init-$(timestamp_utc)/results}"
WORKSHEET_OUT="$OUTPUT_DIR/controlled-public-config-worksheet.md"
CHECK_OUT="$OUTPUT_DIR/controlled-public-config-check.md"

mkdir -p "$OUTPUT_DIR"
cd "$PROJECT_ROOT"

echo "== Controlled public config init =="
print_kv "template_file" "$TEMPLATE_FILE"
print_kv "config_file" "$CONFIG_FILE"
print_kv "output_dir" "$OUTPUT_DIR"
print_kv "overwrite" "$OVERWRITE"
print_kv "require_baseline_ready" "$REQUIRE_BASELINE_READY"

if [[ ! -f "$TEMPLATE_FILE" ]]; then
  print_kv "controlled_public_config_init" "blocked(template_missing)"
  exit 1
fi

INIT_STATUS="exists"
if [[ -f "$CONFIG_FILE" && "$OVERWRITE" != "1" ]]; then
  INIT_STATUS="exists"
elif [[ -f "$CONFIG_FILE" && "$OVERWRITE" == "1" ]]; then
  cp "$TEMPLATE_FILE" "$CONFIG_FILE"
  chmod 600 "$CONFIG_FILE" 2>/dev/null || true
  INIT_STATUS="overwritten"
else
  mkdir -p "$(dirname "$CONFIG_FILE")"
  cp "$TEMPLATE_FILE" "$CONFIG_FILE"
  chmod 600 "$CONFIG_FILE" 2>/dev/null || true
  INIT_STATUS="created"
fi

python3 tools/build_controlled_public_config_worksheet.py \
  --config "$CONFIG_FILE" \
  --output "$WORKSHEET_OUT"

CHECK_EXIT=0
python3 tools/check_controlled_public_config.py \
  --config "$CONFIG_FILE" \
  --output "$CHECK_OUT" \
  --require-baseline-ready || CHECK_EXIT=$?

print_kv "init_status" "$INIT_STATUS"
print_kv "worksheet" "$WORKSHEET_OUT"
print_kv "config_check" "$CHECK_OUT"
print_kv "baseline_check_exit" "$CHECK_EXIT"

if [[ "$CHECK_EXIT" == "0" ]]; then
  echo "controlled_public_config_init=ready"
  exit 0
fi

if [[ "$REQUIRE_BASELINE_READY" == "1" ]]; then
  echo "controlled_public_config_init=blocked"
  exit "$CHECK_EXIT"
fi

echo "controlled_public_config_init=needs_edit"
exit 0
