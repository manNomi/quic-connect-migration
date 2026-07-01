#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LSQUIC_DIR="${LSQUIC_DIR:-/private/tmp/quic-cm-scan-repos/lsquic}"
BUILD_DIR="${LSQUIC_BUILD_DIR:-$LSQUIC_DIR/build-local}"
RUN_ID="${RUN_ID:-lsquic-nat-rebinding-demo-$(date -u +%Y%m%dT%H%M%SZ)}"
HOSTNAME="${HOSTNAME:-www.example.com}"
PAYLOAD_PATH="${PAYLOAD_PATH:-/file-1M}"
SERVER_RATE="${SERVER_RATE:-160000}"
SWITCH_AFTER_SECONDS="${SWITCH_AFTER_SECONDS:-0.75}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT_DIR/harness/results/$RUN_ID}"

SERVER="$BUILD_DIR/bin/http_server"
CLIENT="$BUILD_DIR/bin/http_client"

if [[ ! -x "$SERVER" || ! -x "$CLIENT" ]]; then
  echo "missing LSQUIC http_server/http_client under $BUILD_DIR" >&2
  exit 2
fi

mkdir -p "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/logs"

read -r SERVER_PORT PROXY_PORT < <(
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
PROXY_PID=""

cleanup() {
  for pid in "$PROXY_PID" "$SERVER_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup EXIT

(
  "$SERVER" \
    -c "$HOSTNAME,$ARTIFACT_DIR/certs/cert.pem,$ARTIFACT_DIR/certs/key.pem" \
    -s "127.0.0.1:$SERVER_PORT" \
    -o allow_migration=1 \
    -n 1 \
    -x "$SERVER_RATE" \
    -L debug \
    >"$ARTIFACT_DIR/logs/server.stdout" \
    2>"$ARTIFACT_DIR/logs/server.stderr"
  echo $? >"$ARTIFACT_DIR/server.exit"
) &
SERVER_PID=$!

python3 - "$ARTIFACT_DIR" "$PROXY_PORT" "$SERVER_PORT" "$SWITCH_AFTER_SECONDS" >"$ARTIFACT_DIR/logs/proxy.stdout" 2>"$ARTIFACT_DIR/logs/proxy.stderr" <<'PY' &
import json
import os
import select
import signal
import socket
import sys
import time

artifact_dir = sys.argv[1]
proxy_port = int(sys.argv[2])
server_port = int(sys.argv[3])
switch_after = float(sys.argv[4])

client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_sock.bind(("127.0.0.1", proxy_port))
client_sock.setblocking(False)

upstreams = []
for _ in range(2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 0))
    sock.setblocking(False)
    upstreams.append(sock)

server_addr = ("127.0.0.1", server_port)
client_addr = None
first_seen = None
active = 0
switched_at = None
c2s_packets = 0
s2c_packets = [0, 0]
c2s_bytes = 0
s2c_bytes = [0, 0]
events = []
stop = False

def on_signal(signum, frame):
    global stop
    stop = True

signal.signal(signal.SIGTERM, on_signal)
signal.signal(signal.SIGINT, on_signal)

def emit(event, **fields):
    record = {"t": round(time.monotonic(), 6), "event": event, **fields}
    events.append(record)
    print(json.dumps(record, sort_keys=True), flush=True)

emit(
    "proxy_start",
    listen_port=proxy_port,
    server_port=server_port,
    upstream0_port=upstreams[0].getsockname()[1],
    upstream1_port=upstreams[1].getsockname()[1],
    switch_after_seconds=switch_after,
)

while not stop:
    sockets = [client_sock, *upstreams]
    readable, _, _ = select.select(sockets, [], [], 0.1)
    now = time.monotonic()
    if first_seen and now - first_seen > 30:
        emit("proxy_timeout")
        break

    for sock in readable:
        if sock is client_sock:
            try:
                data, addr = client_sock.recvfrom(65535)
            except BlockingIOError:
                continue
            if client_addr is None:
                client_addr = addr
                first_seen = now
                emit("client_seen", client_host=addr[0], client_port=addr[1])
            elif addr != client_addr:
                emit("unexpected_client_addr", client_host=addr[0], client_port=addr[1])
                client_addr = addr

            if first_seen and active == 0 and now - first_seen >= switch_after:
                active = 1
                switched_at = now
                emit(
                    "upstream_rebind",
                    after_c2s_packets=c2s_packets,
                    new_upstream_port=upstreams[1].getsockname()[1],
                    old_upstream_port=upstreams[0].getsockname()[1],
                )

            c2s_packets += 1
            c2s_bytes += len(data)
            upstreams[active].sendto(data, server_addr)
        else:
            idx = upstreams.index(sock)
            try:
                data, _ = sock.recvfrom(65535)
            except BlockingIOError:
                continue
            s2c_packets[idx] += 1
            s2c_bytes[idx] += len(data)
            if client_addr:
                client_sock.sendto(data, client_addr)

summary = {
    "listen_port": proxy_port,
    "server_port": server_port,
    "upstream0_port": upstreams[0].getsockname()[1],
    "upstream1_port": upstreams[1].getsockname()[1],
    "switched": switched_at is not None,
    "c2s_packets": c2s_packets,
    "s2c_packets_upstream0": s2c_packets[0],
    "s2c_packets_upstream1": s2c_packets[1],
    "c2s_bytes": c2s_bytes,
    "s2c_bytes_upstream0": s2c_bytes[0],
    "s2c_bytes_upstream1": s2c_bytes[1],
    "events": events,
}

with open(os.path.join(artifact_dir, "proxy-summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2, sort_keys=True)
PY
PROXY_PID=$!

sleep 1

set +e
"$CLIENT" \
  -H "$HOSTNAME" \
  -s "127.0.0.1:$PROXY_PORT" \
  -p "$PAYLOAD_PATH" \
  -K \
  -L debug \
  >"$ARTIFACT_DIR/logs/client.stdout" \
  2>"$ARTIFACT_DIR/logs/client.stderr"
CLIENT_EXIT=$?
set -e

for _ in $(seq 1 60); do
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

proxy_value() {
  local field="$1"
  python3 - "$ARTIFACT_DIR/proxy-summary.json" "$field" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
value = data.get(sys.argv[2], "")
if isinstance(value, bool):
    print(str(value).lower())
else:
    print(value)
PY
}

rg --no-ignore --text -n \
  "record new path|Schedule migration|PATH_CHALLENGE|PATH_RESPONSE|path validated|switching from path|current path|new path|assigned .*DCID" \
  "$ARTIFACT_DIR/logs/client.stderr" "$ARTIFACT_DIR/logs/server.stderr" \
  >"$ARTIFACT_DIR/logs/migration-grep.log" || true

{
  printf 'run_id=%s\n' "$RUN_ID"
  printf 'artifact_dir=%s\n' "$ARTIFACT_DIR"
  printf 'server_port=%s\n' "$SERVER_PORT"
  printf 'proxy_port=%s\n' "$PROXY_PORT"
  printf 'payload_path=%s\n' "$PAYLOAD_PATH"
  printf 'server_rate=%s\n' "$SERVER_RATE"
  printf 'switch_after_seconds=%s\n' "$SWITCH_AFTER_SECONDS"
  printf 'client_exit=%s\n' "$CLIENT_EXIT"
  printf 'server_exit=%s\n' "$SERVER_EXIT"
  printf 'proxy_switched=%s\n' "$(proxy_value switched)"
  printf 'proxy_c2s_packets=%s\n' "$(proxy_value c2s_packets)"
  printf 'proxy_s2c_packets_upstream0=%s\n' "$(proxy_value s2c_packets_upstream0)"
  printf 'proxy_s2c_packets_upstream1=%s\n' "$(proxy_value s2c_packets_upstream1)"
  printf 'server_record_new_path_count=%s\n' "$(count_matches "record new path" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_schedule_migration_count=%s\n' "$(count_matches "Schedule migration" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_path_validated_count=%s\n' "$(count_matches "path validated|current path validated" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_path_challenge_count=%s\n' "$(count_matches "PATH_CHALLENGE" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'server_path_response_count=%s\n' "$(count_matches "PATH_RESPONSE" "$ARTIFACT_DIR/logs/server.stderr")"
  printf 'client_path_challenge_count=%s\n' "$(count_matches "PATH_CHALLENGE" "$ARTIFACT_DIR/logs/client.stderr")"
  printf 'client_path_response_count=%s\n' "$(count_matches "PATH_RESPONSE" "$ARTIFACT_DIR/logs/client.stderr")"
} | tee "$ARTIFACT_DIR/result.env"

if [[ "$CLIENT_EXIT" != 0 || "$SERVER_EXIT" != 0 ]]; then
  echo "lsquic NAT rebinding demo failed: client_exit=$CLIENT_EXIT server_exit=$SERVER_EXIT" >&2
  exit 1
fi

if ! rg --no-ignore --text -q '"event": "upstream_rebind"' "$ARTIFACT_DIR/logs/proxy.stdout"; then
  echo "missing UDP proxy rebinding event" >&2
  exit 1
fi

if ! rg --no-ignore --text -q "record new path|Schedule migration|path validated|current path validated" "$ARTIFACT_DIR/logs/server.stderr"; then
  echo "missing LSQUIC server path-change evidence" >&2
  exit 1
fi

echo "validation=ok" | tee -a "$ARTIFACT_DIR/result.env"
