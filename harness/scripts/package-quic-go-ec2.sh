#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

REPRO_DIR="$PROJECT_ROOT/experiments/quic-go-min-repro"
PACKAGE_DIR_REL="../../harness/results/packages"
PACKAGE_NAME="${PACKAGE_NAME:-quic-go-min-repro-$(timestamp_utc).tar.gz}"
PACKAGE_DIR_ABS="$HARNESS_DIR/results/packages"

mkdir -p "$PACKAGE_DIR_ABS"

export PACKAGE_DIR="$PACKAGE_DIR_REL"
export PACKAGE_NAME

PACKAGE_PATH_RAW="$("$REPRO_DIR/scripts/package-for-ec2.sh")"
PACKAGE_PATH="$(cd "$(dirname "$PACKAGE_PATH_RAW")" && pwd)/$(basename "$PACKAGE_PATH_RAW")"

MANIFEST="$PACKAGE_DIR_ABS/${PACKAGE_NAME%.tar.gz}.manifest.env"
{
  printf 'package_name=%s\n' "$PACKAGE_NAME"
  printf 'package_path=%s\n' "$PACKAGE_PATH"
  printf 'created_at=%s\n' "$(timestamp_utc)"
  printf 'source_repro_dir=%s\n' "$REPRO_DIR"
} >"$MANIFEST"

echo "package_quic_go_ec2=ok"
print_kv "package_path" "$PACKAGE_PATH"
print_kv "manifest" "$MANIFEST"
