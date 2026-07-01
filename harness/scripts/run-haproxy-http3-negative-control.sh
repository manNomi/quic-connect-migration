#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HAPROXY_BIN="${HAPROXY_BIN:-$(command -v haproxy || true)}"
HAPROXY_SOURCE_DIR="${HAPROXY_SOURCE_DIR:-/private/tmp/quic-cm-scan-repos/haproxy}"
QUICHE_CLIENT="${QUICHE_CLIENT:-/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client}"
CURL_BIN="${CURL_BIN:-/opt/homebrew/opt/curl/bin/curl}"
OPENSSL_BIN="${OPENSSL_BIN:-/opt/homebrew/opt/openssl@3/bin/openssl}"
RUN_ID="${RUN_ID:-haproxy-http3-negative-control-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT_DIR/harness/results/$RUN_ID}"
BODY_TEXT="${BODY_TEXT:-haproxy h3 negative control fresh}"
MIGRATION_IDLE_TIMEOUT_MS="${MIGRATION_IDLE_TIMEOUT_MS:-12000}"

if [[ -z "$HAPROXY_BIN" || ! -x "$HAPROXY_BIN" ]]; then
  echo "missing haproxy binary" >&2
  exit 2
fi

if [[ ! -x "$QUICHE_CLIENT" ]]; then
  echo "missing quiche client: $QUICHE_CLIENT" >&2
  exit 2
fi

if [[ ! -x "$CURL_BIN" ]]; then
  CURL_BIN="$(command -v curl || true)"
fi

if [[ -z "$CURL_BIN" || ! -x "$CURL_BIN" ]]; then
  echo "missing curl binary" >&2
  exit 2
fi

if [[ ! -x "$OPENSSL_BIN" ]]; then
  OPENSSL_BIN="$(command -v openssl || true)"
fi

if [[ -z "$OPENSSL_BIN" || ! -x "$OPENSSL_BIN" ]]; then
  echo "missing openssl binary" >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/conf" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/www"

printf '%s\n' "$BODY_TEXT" >"$ARTIFACT_DIR/www/index.html"

read -r ORIGIN_PORT HAPROXY_PORT < <(
  python3 - <<'PY'
import socket
socks = []
ports = []
for sock_type in (socket.SOCK_STREAM, socket.SOCK_DGRAM):
    sock = socket.socket(socket.AF_INET, sock_type)
    sock.bind(("127.0.0.1", 0))
    ports.append(sock.getsockname()[1])
    socks.append(sock)
print(*ports)
PY
)

{
  printf 'haproxy_bin=%s\n' "$HAPROXY_BIN"
  printf 'quiche_client=%s\n' "$QUICHE_CLIENT"
  printf 'curl_bin=%s\n' "$CURL_BIN"
  printf 'openssl_bin=%s\n' "$OPENSSL_BIN"
  printf 'origin_port=%s\n' "$ORIGIN_PORT"
  printf 'haproxy_port=%s\n' "$HAPROXY_PORT"
  if [[ -d "$HAPROXY_SOURCE_DIR/.git" ]]; then
    printf 'haproxy_source_dir=%s\n' "$HAPROXY_SOURCE_DIR"
    printf 'haproxy_source_commit=%s\n' "$(git -C "$HAPROXY_SOURCE_DIR" rev-parse HEAD)"
    printf 'haproxy_source_date=%s\n' "$(git -C "$HAPROXY_SOURCE_DIR" show -s --format=%cI HEAD)"
    printf 'haproxy_source_subject=%s\n' "$(git -C "$HAPROXY_SOURCE_DIR" show -s --format=%s HEAD)"
  fi
} >"$ARTIFACT_DIR/source.env"

"$HAPROXY_BIN" -vv >"$ARTIFACT_DIR/logs/haproxy-version.txt" 2>&1
"$CURL_BIN" -V >"$ARTIFACT_DIR/logs/curl-version.txt" 2>&1 || true

"$OPENSSL_BIN" req -x509 -newkey rsa:2048 -sha256 -days 1 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
  -keyout "$ARTIFACT_DIR/certs/key.pem" \
  -out "$ARTIFACT_DIR/certs/cert.pem" \
  >"$ARTIFACT_DIR/logs/openssl.log" \
  2>&1

cat "$ARTIFACT_DIR/certs/cert.pem" "$ARTIFACT_DIR/certs/key.pem" >"$ARTIFACT_DIR/certs/haproxy.pem"

cat >"$ARTIFACT_DIR/conf/haproxy.cfg" <<EOF
global
    log stdout format raw local0 debug
    maxconn 1000

defaults
    log global
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s

frontend h3
    bind quic4@127.0.0.1:$HAPROXY_PORT ssl crt $ARTIFACT_DIR/certs/haproxy.pem alpn h3
    default_backend origin

backend origin
    server s1 127.0.0.1:$ORIGIN_PORT
EOF

"$HAPROXY_BIN" -c -f "$ARTIFACT_DIR/conf/haproxy.cfg" \
  >"$ARTIFACT_DIR/logs/haproxy-config-check.stdout" \
  2>"$ARTIFACT_DIR/logs/haproxy-config-check.stderr"

ORIGIN_PID=""
HAPROXY_PID=""

cleanup() {
  for pid in "$HAPROXY_PID" "$ORIGIN_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT

python3 -m http.server "$ORIGIN_PORT" --bind 127.0.0.1 --directory "$ARTIFACT_DIR/www" \
  >"$ARTIFACT_DIR/logs/origin.log" \
  2>&1 &
ORIGIN_PID=$!

"$HAPROXY_BIN" -f "$ARTIFACT_DIR/conf/haproxy.cfg" -db \
  >"$ARTIFACT_DIR/logs/haproxy.log" \
  2>&1 &
HAPROXY_PID=$!

for _ in $(seq 1 100); do
  if kill -0 "$ORIGIN_PID" 2>/dev/null && kill -0 "$HAPROXY_PID" 2>/dev/null; then
    sleep 0.05
  else
    echo "origin or haproxy exited before client run" >&2
    exit 1
  fi
done

set +e
"$CURL_BIN" --http3-only -k -v "https://127.0.0.1:$HAPROXY_PORT/" \
  >"$ARTIFACT_DIR/logs/curl-http3.out" \
  2>"$ARTIFACT_DIR/logs/curl-http3.err"
CURL_EXIT=$?

RUST_LOG=info "$QUICHE_CLIENT" \
  --no-verify \
  --http-version HTTP/3 \
  --wire-version 1 \
  "https://127.0.0.1:$HAPROXY_PORT/" \
  >"$ARTIFACT_DIR/logs/quiche-baseline.out" \
  2>"$ARTIFACT_DIR/logs/quiche-baseline.err"
BASELINE_EXIT=$?

QLOGDIR="$ARTIFACT_DIR/qlog" RUST_LOG=info "$QUICHE_CLIENT" \
  --no-verify \
  --http-version HTTP/3 \
  --wire-version 1 \
  --idle-timeout "$MIGRATION_IDLE_TIMEOUT_MS" \
  --enable-active-migration \
  --perform-migration \
  "https://127.0.0.1:$HAPROXY_PORT/" \
  >"$ARTIFACT_DIR/logs/quiche-migration.out" \
  2>"$ARTIFACT_DIR/logs/quiche-migration.err"
MIGRATION_EXIT=$?
set -e

cleanup
trap - EXIT

count_matches() {
  local pattern="$1"
  shift
  (rg --no-ignore --text "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
}

CURL_HTTP3_COUNT="$(count_matches "using HTTP/3|HTTP/3 200" "$ARTIFACT_DIR/logs/curl-http3.err")"
CURL_BODY_COUNT="$(count_matches "$BODY_TEXT" "$ARTIFACT_DIR/logs/curl-http3.out")"
BASELINE_BODY_COUNT="$(count_matches "$BODY_TEXT" "$ARTIFACT_DIR/logs/quiche-baseline.out")"
BASELINE_RESPONSE_COUNT="$(count_matches "1/1 response\\(s\\) received" "$ARTIFACT_DIR/logs/quiche-baseline.err")"
BASELINE_VALID_ACTIVE_COUNT="$(count_matches "validation_state=Validated active=true" "$ARTIFACT_DIR/logs/quiche-baseline.err")"
MIGRATION_FAILED_LOG_COUNT="$(count_matches "Path .* failed validation" "$ARTIFACT_DIR/logs/quiche-migration.err")"
MIGRATION_FAILED_INACTIVE_COUNT="$(count_matches "validation_state=Failed active=false" "$ARTIFACT_DIR/logs/quiche-migration.err")"
MIGRATION_ORIGINAL_ACTIVE_COUNT="$(count_matches "validation_state=Validated active=true" "$ARTIFACT_DIR/logs/quiche-migration.err")"
QLOG_PATH_CHALLENGE_COUNT="$(count_matches "path_challenge" "$ARTIFACT_DIR/qlog")"
QLOG_PATH_RESPONSE_COUNT="$(count_matches "path_response" "$ARTIFACT_DIR/qlog")"

rg --no-ignore --text -n \
  "HTTP/3 200|using HTTP/3|1/1 response|failed validation|validation_state=|path_challenge|path_response" \
  "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/qlog" \
  >"$ARTIFACT_DIR/logs/negative-control-grep.log" || true

{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'origin_port=%s\n' "$ORIGIN_PORT"
  printf 'haproxy_port=%s\n' "$HAPROXY_PORT"
  printf 'curl_exit=%s\n' "$CURL_EXIT"
  printf 'curl_http3_count=%s\n' "$CURL_HTTP3_COUNT"
  printf 'curl_body_count=%s\n' "$CURL_BODY_COUNT"
  printf 'quiche_baseline_exit=%s\n' "$BASELINE_EXIT"
  printf 'quiche_baseline_body_count=%s\n' "$BASELINE_BODY_COUNT"
  printf 'quiche_baseline_response_count=%s\n' "$BASELINE_RESPONSE_COUNT"
  printf 'quiche_baseline_valid_active_count=%s\n' "$BASELINE_VALID_ACTIVE_COUNT"
  printf 'quiche_migration_exit=%s\n' "$MIGRATION_EXIT"
  printf 'quiche_migration_failed_log_count=%s\n' "$MIGRATION_FAILED_LOG_COUNT"
  printf 'quiche_migration_failed_inactive_count=%s\n' "$MIGRATION_FAILED_INACTIVE_COUNT"
  printf 'quiche_migration_original_active_count=%s\n' "$MIGRATION_ORIGINAL_ACTIVE_COUNT"
  printf 'qlog_path_challenge_count=%s\n' "$QLOG_PATH_CHALLENGE_COUNT"
  printf 'qlog_path_response_count=%s\n' "$QLOG_PATH_RESPONSE_COUNT"
} | tee "$ARTIFACT_DIR/result.env"

if [[ "$CURL_EXIT" != 0 || "$CURL_HTTP3_COUNT" -lt 1 || "$CURL_BODY_COUNT" -lt 1 ]]; then
  echo "curl HTTP/3 baseline failed" >&2
  exit 1
fi

if [[ "$BASELINE_EXIT" != 0 || "$BASELINE_RESPONSE_COUNT" -lt 1 || "$BASELINE_BODY_COUNT" -lt 1 || "$BASELINE_VALID_ACTIVE_COUNT" -lt 1 ]]; then
  echo "quiche no-migration baseline failed" >&2
  exit 1
fi

if [[ "$MIGRATION_FAILED_LOG_COUNT" -lt 1 || "$MIGRATION_FAILED_INACTIVE_COUNT" -lt 1 ]]; then
  echo "missing quiche migration failure evidence" >&2
  exit 1
fi

if [[ "$MIGRATION_ORIGINAL_ACTIVE_COUNT" -lt 1 ]]; then
  echo "missing original path active evidence" >&2
  exit 1
fi

if [[ "$QLOG_PATH_CHALLENGE_COUNT" -lt 1 || "$QLOG_PATH_RESPONSE_COUNT" -ne 0 ]]; then
  echo "unexpected qlog path challenge/response evidence: challenge=$QLOG_PATH_CHALLENGE_COUNT response=$QLOG_PATH_RESPONSE_COUNT" >&2
  exit 1
fi

echo "validation=ok_negative_control" | tee -a "$ARTIFACT_DIR/result.env"
