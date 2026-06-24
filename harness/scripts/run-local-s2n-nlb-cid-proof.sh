#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CRATE_DIR="$ROOT_DIR/experiments/s2n-quic-nlb-cid-provider"
RESULT_DIR="${1:-$ROOT_DIR/experiments/s2n-quic-nlb-cid-provider/results/local-data-plane-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "$RESULT_DIR"

cargo test --manifest-path "$CRATE_DIR/Cargo.toml" | tee "$RESULT_DIR/cargo-test.log"
cargo run \
  --manifest-path "$CRATE_DIR/Cargo.toml" \
  --bin local_data_plane_proof \
  -- "$RESULT_DIR" | tee "$RESULT_DIR/run.log"

echo "result=$RESULT_DIR/result.json"
