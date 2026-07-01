#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NGINX_DIR="${NGINX_DIR:-/private/tmp/quic-cm-scan-repos/nginx}"
NGINX_BUILD_DIR="${NGINX_BUILD_DIR:-$NGINX_DIR/build-quic-runtime}"
NGINX_PREFIX="${NGINX_PREFIX:-/private/tmp/quic-cm-nginx-runtime}"
QUICHE_CLIENT="${QUICHE_CLIENT:-/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client}"
OPENSSL_BIN="${OPENSSL_BIN:-/opt/local/bin/openssl}"
RUN_ID="${RUN_ID:-nginx-quic-active-migration-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT_DIR/harness/results/$RUN_ID}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
NGINX_QUIC_BPF="${NGINX_QUIC_BPF:-0}"

NGINX_BIN="$NGINX_BUILD_DIR/nginx"
HOST="127.0.0.1"

if [[ ! -d "$NGINX_DIR" ]]; then
  echo "missing nginx source directory: $NGINX_DIR" >&2
  exit 2
fi

if [[ ! -x "$QUICHE_CLIENT" ]]; then
  echo "missing quiche client: $QUICHE_CLIENT" >&2
  exit 2
fi

if [[ ! -x "$OPENSSL_BIN" ]]; then
  OPENSSL_BIN="$(command -v openssl || true)"
fi

if [[ -z "$OPENSSL_BIN" || ! -x "$OPENSSL_BIN" ]]; then
  echo "missing openssl binary" >&2
  exit 2
fi

mkdir -p \
  "$ARTIFACT_DIR/certs" \
  "$ARTIFACT_DIR/client" \
  "$ARTIFACT_DIR/conf" \
  "$ARTIFACT_DIR/html" \
  "$ARTIFACT_DIR/logs"

read -r PORT < <(
  python3 - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
PY
)

{
  printf 'nginx_dir=%s\n' "$NGINX_DIR"
  printf 'nginx_build_dir=%s\n' "$NGINX_BUILD_DIR"
  printf 'nginx_prefix=%s\n' "$NGINX_PREFIX"
  printf 'quiche_client=%s\n' "$QUICHE_CLIENT"
  printf 'openssl_bin=%s\n' "$OPENSSL_BIN"
  printf 'payload_bytes=%s\n' "$PAYLOAD_BYTES"
  printf 'nginx_quic_bpf=%s\n' "$NGINX_QUIC_BPF"
  printf 'source_commit=%s\n' "$(git -C "$NGINX_DIR" rev-parse HEAD)"
  printf 'source_date=%s\n' "$(git -C "$NGINX_DIR" show -s --format=%cI HEAD)"
  printf 'source_subject=%s\n' "$(git -C "$NGINX_DIR" show -s --format=%s HEAD)"
} >"$ARTIFACT_DIR/source.env"

if [[ ! -x "$NGINX_BIN" ]]; then
  (
    cd "$NGINX_DIR"
    auto/configure \
      --builddir="$(basename "$NGINX_BUILD_DIR")" \
      --prefix="$NGINX_PREFIX" \
      --with-http_ssl_module \
      --with-http_v3_module \
      --with-debug \
      --with-cc-opt='-I/opt/local/include' \
      --with-ld-opt='-L/opt/local/lib -Wl,-rpath,/opt/local/lib' \
      >"$ARTIFACT_DIR/logs/nginx-configure.log" \
      2>"$ARTIFACT_DIR/logs/nginx-configure.err"
    make -f "$NGINX_BUILD_DIR/Makefile" -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)" \
      >"$ARTIFACT_DIR/logs/nginx-make.log" \
      2>"$ARTIFACT_DIR/logs/nginx-make.err"
  )
fi

"$NGINX_BIN" -V >"$ARTIFACT_DIR/logs/nginx-version.txt" 2>&1

"$OPENSSL_BIN" req -x509 -newkey rsa:2048 -sha256 -days 1 -nodes \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
  -keyout "$ARTIFACT_DIR/certs/key.pem" \
  -out "$ARTIFACT_DIR/certs/cert.pem" \
  >"$ARTIFACT_DIR/logs/openssl.log" \
  2>&1

python3 - "$ARTIFACT_DIR/html/file-1M" "$PAYLOAD_BYTES" <<'PY'
import os
import sys
path = sys.argv[1]
size = int(sys.argv[2])
pattern = b"nginx-quic-active-migration-demo\n"
with open(path, "wb") as fh:
    written = 0
    while written < size:
        chunk = pattern[: min(len(pattern), size - written)]
        fh.write(chunk)
        written += len(chunk)
PY

MAIN_QUIC_BPF_DIRECTIVE=""
LISTEN_REUSEPORT=""
if [[ "$NGINX_QUIC_BPF" == "1" ]]; then
  MAIN_QUIC_BPF_DIRECTIVE="quic_bpf on;"
  LISTEN_REUSEPORT=" reuseport"
fi

cat >"$ARTIFACT_DIR/conf/nginx.conf" <<EOF
worker_processes 1;
error_log $ARTIFACT_DIR/logs/error.log debug;
pid $ARTIFACT_DIR/logs/nginx.pid;
$MAIN_QUIC_BPF_DIRECTIVE

events {
    worker_connections 1024;
}

http {
    access_log $ARTIFACT_DIR/logs/access.log combined;

    server {
        listen $HOST:$PORT quic$LISTEN_REUSEPORT;
        http3 on;
        quic_retry off;

        ssl_protocols TLSv1.3;
        ssl_certificate $ARTIFACT_DIR/certs/cert.pem;
        ssl_certificate_key $ARTIFACT_DIR/certs/key.pem;

        root $ARTIFACT_DIR/html;

        location = / {
            return 200 'nginx h3 ok\n';
        }

        location = /file-1M {
        }
    }
}
EOF

"$NGINX_BIN" -p "$ARTIFACT_DIR" -c conf/nginx.conf -t \
  >"$ARTIFACT_DIR/logs/nginx-test.stdout" \
  2>"$ARTIFACT_DIR/logs/nginx-test.stderr"

NGINX_PID=""
cleanup() {
  if [[ -n "$NGINX_PID" ]] && kill -0 "$NGINX_PID" 2>/dev/null; then
    kill "$NGINX_PID" 2>/dev/null || true
    wait "$NGINX_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

"$NGINX_BIN" -p "$ARTIFACT_DIR" -c conf/nginx.conf -g "daemon off; master_process off;" \
  >"$ARTIFACT_DIR/logs/nginx.stdout" \
  2>"$ARTIFACT_DIR/logs/nginx.stderr" &
NGINX_PID=$!

for _ in $(seq 1 100); do
  if [[ -s "$ARTIFACT_DIR/logs/error.log" ]] && rg --no-ignore --text -q "start worker process|worker process" "$ARTIFACT_DIR/logs/error.log"; then
    break
  fi
  if ! kill -0 "$NGINX_PID" 2>/dev/null; then
    echo "nginx exited before client run" >&2
    exit 1
  fi
  sleep 0.05
done

set +e
RUST_LOG=info "$QUICHE_CLIENT" \
  --no-verify \
  --http-version HTTP/3 \
  --wire-version 1 \
  --enable-active-migration \
  --perform-migration \
  "https://$HOST:$PORT/file-1M" \
  >"$ARTIFACT_DIR/client/response.bin" \
  2>"$ARTIFACT_DIR/logs/client.stderr"
CLIENT_EXIT=$?
set -e

cleanup
trap - EXIT

count_matches() {
  local pattern="$1"
  shift
  (rg --no-ignore --text "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
}

CLIENT_RESPONSE_BYTES="$(wc -c <"$ARTIFACT_DIR/client/response.bin" | tr -d ' ')"
ACCESS_GET_FILE_COUNT="$(count_matches "GET /file-1M HTTP/3\\.0\" 200" "$ARTIFACT_DIR/logs/access.log")"
SERVER_PATH_SEQ1_CREATED_COUNT="$(count_matches "quic path seq:1 created" "$ARTIFACT_DIR/logs/error.log")"
SERVER_PATH_SEQ1_VALIDATED_COUNT="$(count_matches "quic path seq:1 .*successfully validated|quic path seq:1 is validated" "$ARTIFACT_DIR/logs/error.log")"
SERVER_PATH_CHALLENGE_RX_COUNT="$(count_matches "frame rx .*PATH_CHALLENGE" "$ARTIFACT_DIR/logs/error.log")"
SERVER_PATH_RESPONSE_TX_COUNT="$(count_matches "frame tx .*PATH_RESPONSE" "$ARTIFACT_DIR/logs/error.log")"
SERVER_PATH_CHALLENGE_TX_COUNT="$(count_matches "frame tx .*PATH_CHALLENGE" "$ARTIFACT_DIR/logs/error.log")"
SERVER_PATH_RESPONSE_RX_COUNT="$(count_matches "frame rx .*PATH_RESPONSE" "$ARTIFACT_DIR/logs/error.log")"
CLIENT_PATH_VALIDATED_COUNT="$(count_matches "Path .* is now validated" "$ARTIFACT_DIR/logs/client.stderr")"
CLIENT_MIGRATION_LOG_COUNT="$(count_matches "performing migration|migration" "$ARTIFACT_DIR/logs/client.stderr")"
CLIENT_ACTIVE_TRUE_COUNT="$(count_matches "active=true" "$ARTIFACT_DIR/logs/client.stderr")"
CLIENT_ACTIVE_FALSE_COUNT="$(count_matches "active=false" "$ARTIFACT_DIR/logs/client.stderr")"
SERVER_DISABLE_ACTIVE_MIGRATION_ZERO_COUNT="$(count_matches "quic tp disable active migration: 0" "$ARTIFACT_DIR/logs/error.log")"
SERVER_QUIC_BPF_LOG_COUNT="$(count_matches "quic_bpf" "$ARTIFACT_DIR/logs/error.log" "$ARTIFACT_DIR/logs/nginx.stderr")"

rg --no-ignore --text -n \
  "disable active migration|quic path seq:1|PATH_CHALLENGE|PATH_RESPONSE|successfully validated|is now validated|active=true|active=false|migration|quic_bpf" \
  "$ARTIFACT_DIR/logs/error.log" \
  "$ARTIFACT_DIR/logs/client.stderr" \
  "$ARTIFACT_DIR/logs/nginx.stderr" \
  >"$ARTIFACT_DIR/logs/migration-grep.log" || true

{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'host=%s\n' "$HOST"
  printf 'port=%s\n' "$PORT"
  printf 'nginx_quic_bpf=%s\n' "$NGINX_QUIC_BPF"
  printf 'client_exit=%s\n' "$CLIENT_EXIT"
  printf 'payload_bytes=%s\n' "$PAYLOAD_BYTES"
  printf 'client_response_bytes=%s\n' "$CLIENT_RESPONSE_BYTES"
  printf 'access_get_file_count=%s\n' "$ACCESS_GET_FILE_COUNT"
  printf 'server_path_seq1_created_count=%s\n' "$SERVER_PATH_SEQ1_CREATED_COUNT"
  printf 'server_path_seq1_validated_count=%s\n' "$SERVER_PATH_SEQ1_VALIDATED_COUNT"
  printf 'server_path_challenge_rx_count=%s\n' "$SERVER_PATH_CHALLENGE_RX_COUNT"
  printf 'server_path_response_tx_count=%s\n' "$SERVER_PATH_RESPONSE_TX_COUNT"
  printf 'server_path_challenge_tx_count=%s\n' "$SERVER_PATH_CHALLENGE_TX_COUNT"
  printf 'server_path_response_rx_count=%s\n' "$SERVER_PATH_RESPONSE_RX_COUNT"
  printf 'server_disable_active_migration_zero_count=%s\n' "$SERVER_DISABLE_ACTIVE_MIGRATION_ZERO_COUNT"
  printf 'client_path_validated_count=%s\n' "$CLIENT_PATH_VALIDATED_COUNT"
  printf 'client_migration_log_count=%s\n' "$CLIENT_MIGRATION_LOG_COUNT"
  printf 'client_active_true_count=%s\n' "$CLIENT_ACTIVE_TRUE_COUNT"
  printf 'client_active_false_count=%s\n' "$CLIENT_ACTIVE_FALSE_COUNT"
  printf 'server_quic_bpf_log_count=%s\n' "$SERVER_QUIC_BPF_LOG_COUNT"
} | tee "$ARTIFACT_DIR/result.env"

if [[ "$CLIENT_EXIT" != 0 ]]; then
  echo "nginx active migration demo failed: client_exit=$CLIENT_EXIT" >&2
  exit 1
fi

if [[ "$CLIENT_RESPONSE_BYTES" != "$PAYLOAD_BYTES" ]]; then
  echo "unexpected response size: got $CLIENT_RESPONSE_BYTES want $PAYLOAD_BYTES" >&2
  exit 1
fi

if [[ "$ACCESS_GET_FILE_COUNT" -lt 1 ]]; then
  echo "missing nginx HTTP/3 access log for /file-1M" >&2
  exit 1
fi

if [[ "$SERVER_PATH_SEQ1_CREATED_COUNT" -lt 1 || "$SERVER_PATH_SEQ1_VALIDATED_COUNT" -lt 1 ]]; then
  echo "missing nginx path seq:1 creation/validation evidence" >&2
  exit 1
fi

if [[ "$SERVER_PATH_CHALLENGE_RX_COUNT" -lt 1 || "$SERVER_PATH_RESPONSE_TX_COUNT" -lt 1 ]]; then
  echo "missing server response to client PATH_CHALLENGE" >&2
  exit 1
fi

if [[ "$CLIENT_PATH_VALIDATED_COUNT" -lt 1 ]]; then
  echo "missing client path validation evidence" >&2
  exit 1
fi

echo "validation=ok" | tee -a "$ARTIFACT_DIR/result.env"
