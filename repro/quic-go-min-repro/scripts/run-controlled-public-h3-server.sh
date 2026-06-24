#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

RUN_ID="${RUN_ID:-controlled-public-h3-server-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
PUBLIC_ORIGIN_HOST="${PUBLIC_ORIGIN_HOST:?set PUBLIC_ORIGIN_HOST, e.g. h3.example.com}"
TLS_CERT_FILE="${TLS_CERT_FILE:?set TLS_CERT_FILE to a WebPKI certificate chain file}"
TLS_KEY_FILE="${TLS_KEY_FILE:?set TLS_KEY_FILE to the matching private key file}"
PUBLIC_ORIGIN_PORT="${PUBLIC_ORIGIN_PORT:-443}"
LISTEN_ADDR="${LISTEN_ADDR:-0.0.0.0:${PUBLIC_ORIGIN_PORT}}"
TCP_ADDR="${TCP_ADDR:-0.0.0.0:${PUBLIC_ORIGIN_PORT}}"
ALT_SVC="${ALT_SVC:-h3=\":${PUBLIC_ORIGIN_PORT}\"; ma=60}"
EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-2}"
TIMEOUT="${TIMEOUT:-300s}"
COMPLETION_GRACE="${COMPLETION_GRACE:-2s}"

mkdir -p "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/logs"

if [[ ! -r "$TLS_CERT_FILE" ]]; then
  echo "certificate file is not readable: $TLS_CERT_FILE" >&2
  exit 2
fi
if [[ ! -r "$TLS_KEY_FILE" ]]; then
  echo "key file is not readable: $TLS_KEY_FILE" >&2
  exit 2
fi

python3 - \
  "$ARTIFACT_DIR/results/server-public-origin-metadata.json" \
  "$RUN_ID" \
  "$PUBLIC_ORIGIN_HOST" \
  "$PUBLIC_ORIGIN_PORT" \
  "$LISTEN_ADDR" \
  "$TCP_ADDR" \
  "$ALT_SVC" \
  "$EXPECTED_REQUESTS" <<'PY'
import json
import sys

output, run_id, host, port, listen_addr, tcp_addr, alt_svc, expected_requests = sys.argv[1:]
metadata = {
    "run_id": run_id,
    "public_origin_host": host,
    "public_origin_port": port,
    "listen_addr": listen_addr,
    "tcp_addr": tcp_addr,
    "alt_svc": alt_svc,
    "expected_requests": expected_requests,
}
with open(output, "w", encoding="utf-8") as fp:
    json.dump(metadata, fp, indent=2)
    fp.write("\n")
PY

QUIC_CM_CERT_FILE="$TLS_CERT_FILE" \
QUIC_CM_KEY_FILE="$TLS_KEY_FILE" \
ARTIFACT_DIR="$ARTIFACT_DIR" \
LISTEN_ADDR="$LISTEN_ADDR" \
TCP_ADDR="$TCP_ADDR" \
ALT_SVC="$ALT_SVC" \
EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
TIMEOUT="$TIMEOUT" \
COMPLETION_GRACE="$COMPLETION_GRACE" \
./scripts/run-h3-server.sh
