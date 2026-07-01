#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LSQUIC_DIR="${LSQUIC_DIR:-/private/tmp/quic-cm-scan-repos/lsquic}"
BUILD_DIR="${LSQUIC_BUILD_DIR:-$LSQUIC_DIR/build-local}"
RUN_ID="${RUN_ID:-lsquic-preferred-address-demo-$(date -u +%Y%m%dT%H%M%SZ)}"
PAYLOAD_PATH="${PAYLOAD_PATH:-/file-1M}"
HOSTNAME="${HOSTNAME:-www.example.com}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT_DIR/harness/results/$RUN_ID}"

SERVER="$BUILD_DIR/bin/http_server"
CLIENT="$BUILD_DIR/bin/http_client"

if [[ ! -x "$SERVER" || ! -x "$CLIENT" ]]; then
  echo "missing LSQUIC http_server/http_client under $BUILD_DIR" >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/out"

read -r INITIAL_PORT PREFERRED_PORT < <(
  python3 - <<'PY'
import socket
socks = []
ports = []
for _ in range(2):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    ports.append(s.getsockname()[1])
    socks.append(s)
print(*ports)
PY
)

openssl req -x509 -newkey rsa:2048 -sha256 -days 1 -nodes \
  -subj "/CN=$HOSTNAME" \
  -addext "subjectAltName=DNS:$HOSTNAME,IP:127.0.0.1" \
  -keyout "$ARTIFACT_DIR/certs/key.pem" \
  -out "$ARTIFACT_DIR/certs/cert.pem" \
  >"$ARTIFACT_DIR/logs/openssl.log" 2>&1

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

(
  "$SERVER" \
    -c "$HOSTNAME,$ARTIFACT_DIR/certs/cert.pem,$ARTIFACT_DIR/certs/key.pem" \
    -s "127.0.0.1:$INITIAL_PORT" \
    -s "127.0.0.1:$PREFERRED_PORT" \
    -o "preferred_v4=127.0.0.1:$PREFERRED_PORT" \
    -n 1 \
    -L debug \
    >"$ARTIFACT_DIR/logs/server.stdout" \
    2>"$ARTIFACT_DIR/logs/server.stderr"
  echo $? >"$ARTIFACT_DIR/server.exit"
) &
SERVER_PID=$!

sleep 1

set +e
"$CLIENT" \
  -H "$HOSTNAME" \
  -s "127.0.0.1:$INITIAL_PORT" \
  -p "$PAYLOAD_PATH" \
  -K \
  -L debug \
  >"$ARTIFACT_DIR/logs/client.stdout" \
  2>"$ARTIFACT_DIR/logs/client.stderr"
CLIENT_EXIT=$?
set -e

for _ in $(seq 1 40); do
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    sleep 0.2
  else
    break
  fi
done

cleanup
trap - EXIT

SERVER_EXIT="$(cat "$ARTIFACT_DIR/server.exit" 2>/dev/null || echo missing)"

count_matches() {
  local pattern="$1"
  shift
  rg --no-ignore --text "$pattern" "$@" 2>/dev/null | wc -l | tr -d ' '
}

max_client_read_off="$(
  rg --no-ignore --text "cfcw: read_off goes from [0-9]+ to [0-9]+" "$ARTIFACT_DIR/logs/client.stderr" 2>/dev/null \
    | sed -E 's/.* to ([0-9]+).*/\1/' \
    | sort -n \
    | tail -n 1
)"
max_client_read_off="${max_client_read_off:-0}"

rg --no-ignore --text -n \
  "Schedule migration|PATH_CHALLENGE|PATH_RESPONSE|migration|path 1|new path|record new path|preferred" \
  "$ARTIFACT_DIR/logs/client.stderr" "$ARTIFACT_DIR/logs/server.stderr" \
  >"$ARTIFACT_DIR/logs/migration-grep.log" || true

{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'initial_port=%s\n' "$INITIAL_PORT"
  printf 'preferred_port=%s\n' "$PREFERRED_PORT"
  printf 'payload_path=%s\n' "$PAYLOAD_PATH"
  printf 'client_exit=%s\n' "$CLIENT_EXIT"
  printf 'server_exit=%s\n' "$SERVER_EXIT"
  printf 'client_schedule_migration_count=%s\n' "$(count_matches "Schedule migration to path 1" "$ARTIFACT_DIR/logs/client.stderr")"
  printf 'client_tx_path1_count=%s\n' "$(count_matches "TX packet .*path: 1" "$ARTIFACT_DIR/logs/client.stderr")"
  printf 'server_tx_path1_count=%s\n' "$(count_matches "TX packet .*path: 1" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_tx_stream_path1_count=%s\n' "$(count_matches "TX packet .*STREAM.*path: 1" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'client_path_challenge_count=%s\n' "$(count_matches "PATH_CHALLENGE" "$ARTIFACT_DIR/logs/client.stderr")"
  printf 'client_path_response_count=%s\n' "$(count_matches "PATH_RESPONSE" "$ARTIFACT_DIR/logs/client.stderr")"
  printf 'server_path_challenge_count=%s\n' "$(count_matches "PATH_CHALLENGE" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_path_response_count=%s\n' "$(count_matches "PATH_RESPONSE" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'preferred_address_tp_count=%s\n' "$(count_matches "IPv4 preferred address: 127\\.0\\.0\\.1:$PREFERRED_PORT" "$ARTIFACT_DIR/logs/client.stderr" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'max_client_read_off=%s\n' "$max_client_read_off"
} | tee "$ARTIFACT_DIR/result.env"

if [[ "$CLIENT_EXIT" != 0 || "$SERVER_EXIT" != 0 ]]; then
  echo "lsquic preferred-address demo failed: client_exit=$CLIENT_EXIT server_exit=$SERVER_EXIT" >&2
  exit 1
fi

if ! rg --no-ignore --text -q "Schedule migration to path 1" "$ARTIFACT_DIR/logs/client.stderr"; then
  echo "missing LSQUIC client migration scheduling evidence" >&2
  exit 1
fi

if ! rg --no-ignore --text -q "TX packet .*STREAM.*path: 1" "$ARTIFACT_DIR/logs/server.stderr"; then
  echo "missing LSQUIC HTTP/3 STREAM data on migrated path 1" >&2
  exit 1
fi

echo "validation=ok" | tee -a "$ARTIFACT_DIR/result.env"
