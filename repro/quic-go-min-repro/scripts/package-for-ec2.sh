#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

PACKAGE_DIR="${PACKAGE_DIR:-artifacts/packages}"
PACKAGE_NAME="${PACKAGE_NAME:-quic-go-min-repro-$(date -u +%Y%m%dT%H%M%SZ).tar.gz}"

mkdir -p "$PACKAGE_DIR"

tar \
  --exclude './artifacts/*' \
  --exclude './.DS_Store' \
  -czf "$PACKAGE_DIR/$PACKAGE_NAME" \
  ./go.mod ./go.sum ./cmd ./internal ./scripts

printf '%s\n' "$REPRO_DIR/$PACKAGE_DIR/$PACKAGE_NAME"
