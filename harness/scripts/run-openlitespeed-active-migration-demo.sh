#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

OPENLITESPEED_DIR="${OPENLITESPEED_DIR:-/private/tmp/quic-cm-scan-repos/openlitespeed}"
LSHTTPD_BIN="${LSHTTPD_BIN:-$(command -v lshttpd 2>/dev/null || true)}"
OPENLITESPEED_BIN="${OPENLITESPEED_BIN:-$(command -v openlitespeed 2>/dev/null || true)}"
QUICHE_CLIENT="${QUICHE_CLIENT:-/private/tmp/quic-cm-impl-rerun-20260630/quiche/target/debug/quiche-client}"
OPENSSL_BIN="${OPENSSL_BIN:-$(command -v openssl 2>/dev/null || true)}"
RUN_ID="${RUN_ID:-openlitespeed-active-migration-$(timestamp_utc)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$PROJECT_ROOT/harness/results/$RUN_ID}"
SERVER_ROOT="${SERVER_ROOT:-$ARTIFACT_DIR/server-root}"
HOST="${HOST:-127.0.0.1}"
HOSTNAME="${HOSTNAME:-localhost}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-1048576}"
REQUIRE_LINUX="${REQUIRE_LINUX:-1}"
CONFIG_TEST_ONLY="${CONFIG_TEST_ONLY:-0}"
CLIENT_TIMEOUT_SECONDS="${CLIENT_TIMEOUT_SECONDS:-20}"
SHM_DIR="${SHM_DIR:-/dev/shm}"

LSHTTPD_RUN_BIN="$LSHTTPD_BIN"
if [[ -z "$LSHTTPD_RUN_BIN" && -n "$OPENLITESPEED_BIN" ]]; then
  LSHTTPD_RUN_BIN="$OPENLITESPEED_BIN"
fi

mkdir -p "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/client"

count_matches() {
  local pattern="$1"
  shift
  if command -v rg >/dev/null 2>&1; then
    (rg --no-ignore --text "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
  else
    (grep -E "$pattern" "$@" 2>/dev/null || true) | wc -l | tr -d ' '
  fi
}

grep_migration_lines() {
  local pattern="$1"
  shift
  if command -v rg >/dev/null 2>&1; then
    rg --no-ignore --text -n "$pattern" "$@" 2>/dev/null || true
  else
    grep -H -n -E "$pattern" "$@" 2>/dev/null || true
  fi
}

write_blocked_result() {
  local reason="$1"
  {
    print_kv run_id "$RUN_ID"
    print_kv artifact_dir "$ARTIFACT_DIR"
    print_kv validation "blocked"
    print_kv blocked_reason "$reason"
    print_kv openlitespeed_dir "$OPENLITESPEED_DIR"
    print_kv lshttpd_bin "$LSHTTPD_BIN"
    print_kv openlitespeed_bin "$OPENLITESPEED_BIN"
    print_kv quiche_client "$QUICHE_CLIENT"
    print_kv openssl_bin "$OPENSSL_BIN"
    print_kv system_name "$(uname -s)"
    print_kv system_machine "$(uname -m)"
    print_kv require_linux "$REQUIRE_LINUX"
    print_kv server_root "$SERVER_ROOT"
  } | tee "$ARTIFACT_DIR/result.env"
}

if [[ -z "$LSHTTPD_RUN_BIN" || ! -x "$LSHTTPD_RUN_BIN" ]]; then
  write_blocked_result "missing-openlitespeed-binary"
  echo "missing OpenLiteSpeed binary; set LSHTTPD_BIN or OPENLITESPEED_BIN" >&2
  exit 2
fi

if [[ -z "$QUICHE_CLIENT" || ! -x "$QUICHE_CLIENT" ]]; then
  write_blocked_result "missing-quiche-client"
  echo "missing quiche client: $QUICHE_CLIENT" >&2
  exit 2
fi

if [[ -z "$OPENSSL_BIN" || ! -x "$OPENSSL_BIN" ]]; then
  write_blocked_result "missing-openssl"
  echo "missing openssl binary" >&2
  exit 2
fi

if [[ "$REQUIRE_LINUX" == "1" && "$(uname -s)" != "Linux" ]]; then
  write_blocked_result "linux-runtime-required"
  echo "OpenLiteSpeed QUIC runtime demo is restricted to Linux by default; set REQUIRE_LINUX=0 to override" >&2
  exit 2
fi

if [[ ! -d "$SHM_DIR" || ! -w "$SHM_DIR" ]]; then
  write_blocked_result "missing-writable-quic-shm-dir"
  echo "missing writable QUIC shared-memory directory: $SHM_DIR" >&2
  exit 2
fi

read -r PORT < <(
  python3 - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
PY
)

mkdir -p \
  "$SERVER_ROOT/admin/conf" \
  "$SERVER_ROOT/admin/tmp" \
  "$SERVER_ROOT/cachedata" \
  "$SERVER_ROOT/cert" \
  "$SERVER_ROOT/cgid" \
  "$SERVER_ROOT/conf/vhosts/Example" \
  "$SERVER_ROOT/Example/html" \
  "$SERVER_ROOT/Example/logs" \
  "$SERVER_ROOT/logs" \
  "$SERVER_ROOT/tmp" \
  "$SERVER_ROOT/autoupdate"

"$OPENSSL_BIN" req -x509 -newkey rsa:2048 -sha256 -days 1 -nodes \
  -subj "/CN=$HOSTNAME" \
  -addext "subjectAltName=DNS:$HOSTNAME,IP:127.0.0.1" \
  -keyout "$SERVER_ROOT/cert/server.key" \
  -out "$SERVER_ROOT/cert/server.crt" \
  >"$ARTIFACT_DIR/logs/openssl.log" \
  2>&1

if [[ -f "$OPENLITESPEED_DIR/dist/conf/mime.properties" ]]; then
  cp "$OPENLITESPEED_DIR/dist/conf/mime.properties" "$SERVER_ROOT/conf/mime.properties"
else
  printf 'text/html html htm\napplication/octet-stream bin\n' >"$SERVER_ROOT/conf/mime.properties"
fi

python3 - "$SERVER_ROOT/Example/html/file-1M" "$PAYLOAD_BYTES" <<'PY'
import sys
path = sys.argv[1]
size = int(sys.argv[2])
pattern = b"openlitespeed-quic-active-migration-demo\n"
with open(path, "wb") as fh:
    written = 0
    while written < size:
        chunk = pattern[: min(len(pattern), size - written)]
        fh.write(chunk)
        written += len(chunk)
PY

cat >"$SERVER_ROOT/Example/html/index.html" <<'EOF'
openlitespeed h3 ok
EOF

cat >"$SERVER_ROOT/conf/vhosts/Example/vhconf.conf" <<'EOF'
docRoot $VH_ROOT/html/
enableGzip 0

context / {
  allowBrowse 1
  location $DOC_ROOT/
}

index {
  indexFiles index.html
  autoIndex 0
  useServer 0
}

errorlog $VH_ROOT/logs/error.log {
  logLevel DEBUG
  rollingSize 10M
  useServer 0
}

accessLog $VH_ROOT/logs/access.log {
  rollingSize 10M
  keepDays 1
  compressArchive 0
  logReferer 1
  logUserAgent 1
  useServer 0
}

rewrite {
  enable 0
  logLevel 0
}

accessControl {
  deny
  allow *
}
EOF

cat >"$SERVER_ROOT/conf/httpd_config.conf" <<EOF
serverName                       openlitespeed-quic-cm
user                             $(id -un)
group                            $(id -gn)
priority                         0
autoRestart                      0
chrootPath                       /
enableChroot                     0
mime                             conf/mime.properties
indexFiles                       index.html
disableWebAdmin                  1

errorlog logs/error.log {
  logLevel                       DEBUG
  debugLevel                     9
  rollingSize                    20M
  enableStderrLog                1
}

accessLog logs/access.log {
  rollingSize                    20M
  keepDays                       1
  compressArchive                0
  logReferer                     1
  logUserAgent                   1
}

tuning {
  maxConnections                 1000
  maxSSLConnections              1000
  connTimeout                    300
  maxKeepAliveReq                1000
  keepAliveTimeout               5
  eventDispatcher                best
  maxReqBodySize                 2047M
  enableGzipCompress             0
  quicEnable                     1
  quicShmDir                     $SHM_DIR
}

accessControl {
  allow                          ALL
  deny
}

virtualHost Example {
  vhRoot                         Example/
  allowSymbolLink                1
  enableScript                   0
  restrained                     0
  setUIDMode                     0
  configFile                     conf/vhosts/Example/vhconf.conf
}

listener QUICDemo {
  address                        $HOST:$PORT
  secure                         1
  keyFile                        cert/server.key
  certFile                       cert/server.crt
  enableSpdy                     15
  map                            Example *
}
EOF

{
  print_kv run_id "$RUN_ID"
  print_kv artifact_dir "$ARTIFACT_DIR"
  print_kv server_root "$SERVER_ROOT"
  print_kv openlitespeed_dir "$OPENLITESPEED_DIR"
  print_kv lshttpd_run_bin "$LSHTTPD_RUN_BIN"
  print_kv quiche_client "$QUICHE_CLIENT"
  print_kv openssl_bin "$OPENSSL_BIN"
  print_kv host "$HOST"
  print_kv hostname "$HOSTNAME"
  print_kv port "$PORT"
  print_kv payload_bytes "$PAYLOAD_BYTES"
  print_kv shm_dir "$SHM_DIR"
  if [[ -d "$OPENLITESPEED_DIR/.git" ]]; then
    print_kv openlitespeed_source_commit "$(git -C "$OPENLITESPEED_DIR" rev-parse HEAD)"
    print_kv openlitespeed_source_date "$(git -C "$OPENLITESPEED_DIR" show -s --format=%cI HEAD)"
    print_kv openlitespeed_source_subject "$(git -C "$OPENLITESPEED_DIR" show -s --format=%s HEAD)"
  fi
} >"$ARTIFACT_DIR/source.env"

set +e
LSWS_HOME="$SERVER_ROOT" LSHTTPD_HOME="$SERVER_ROOT" "$LSHTTPD_RUN_BIN" -v \
  >"$ARTIFACT_DIR/logs/lshttpd-version.txt" 2>&1
VERSION_EXIT=$?
LSWS_HOME="$SERVER_ROOT" LSHTTPD_HOME="$SERVER_ROOT" "$LSHTTPD_RUN_BIN" -t \
  >"$ARTIFACT_DIR/logs/config-test.stdout" 2>"$ARTIFACT_DIR/logs/config-test.stderr"
CONFIG_TEST_EXIT=$?
set -e

if [[ "$CONFIG_TEST_ONLY" == "1" || "$CONFIG_TEST_EXIT" != "0" ]]; then
  {
    cat "$ARTIFACT_DIR/source.env"
    print_kv validation "config_test_only"
    print_kv version_exit "$VERSION_EXIT"
    print_kv config_test_exit "$CONFIG_TEST_EXIT"
  } | tee "$ARTIFACT_DIR/result.env"
  if [[ "$CONFIG_TEST_EXIT" != "0" ]]; then
    echo "OpenLiteSpeed config test failed; see $ARTIFACT_DIR/logs/config-test.stderr" >&2
    exit 1
  fi
  exit 0
fi

LSHTTPD_PID=""
cleanup() {
  if [[ -n "$LSHTTPD_PID" ]] && kill -0 "$LSHTTPD_PID" 2>/dev/null; then
    kill "$LSHTTPD_PID" 2>/dev/null || true
    wait "$LSHTTPD_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

LSWS_HOME="$SERVER_ROOT" LSHTTPD_HOME="$SERVER_ROOT" "$LSHTTPD_RUN_BIN" -d \
  >"$ARTIFACT_DIR/logs/lshttpd.stdout" \
  2>"$ARTIFACT_DIR/logs/lshttpd.stderr" &
LSHTTPD_PID=$!

for _ in $(seq 1 100); do
  if ! kill -0 "$LSHTTPD_PID" 2>/dev/null; then
    echo "OpenLiteSpeed exited before client run" >&2
    break
  fi
  if [[ -s "$SERVER_ROOT/logs/error.log" ]] && count_matches "openlitespeed|litespeed|quic|listening|start" "$SERVER_ROOT/logs/error.log" >/dev/null; then
    break
  fi
  sleep 0.1
done

set +e
timeout "$CLIENT_TIMEOUT_SECONDS" "$QUICHE_CLIENT" \
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

CLIENT_RESPONSE_BYTES="$(wc -c <"$ARTIFACT_DIR/client/response.bin" | tr -d ' ')"
ACCESS_GET_FILE_COUNT="$(count_matches "GET /file-1M|file-1M" "$SERVER_ROOT/logs/access.log" "$SERVER_ROOT/Example/logs/access.log")"
SERVER_PATH_CHALLENGE_COUNT="$(count_matches "PATH_CHALLENGE|path challenge" "$SERVER_ROOT/logs/error.log" "$SERVER_ROOT/Example/logs/error.log" "$ARTIFACT_DIR/logs/lshttpd.stderr")"
SERVER_PATH_RESPONSE_COUNT="$(count_matches "PATH_RESPONSE|path response" "$SERVER_ROOT/logs/error.log" "$SERVER_ROOT/Example/logs/error.log" "$ARTIFACT_DIR/logs/lshttpd.stderr")"
SERVER_MIGRATION_COUNT="$(count_matches "migrat|new path|record new path|path validated|Schedule migration" "$SERVER_ROOT/logs/error.log" "$SERVER_ROOT/Example/logs/error.log" "$ARTIFACT_DIR/logs/lshttpd.stderr")"
CLIENT_PATH_VALIDATED_COUNT="$(count_matches "Path .*validated|is now validated|active=true|Connection migrated" "$ARTIFACT_DIR/logs/client.stderr")"
CLIENT_PATH_FAILED_COUNT="$(count_matches "validation_state=Failed|active=false|migration failed|failed" "$ARTIFACT_DIR/logs/client.stderr")"

grep_migration_lines \
  "QUIC|PATH_CHALLENGE|PATH_RESPONSE|migrat|new path|record new path|path validated|Schedule migration|active=true|active=false|validated|failed" \
  "$SERVER_ROOT/logs/error.log" \
  "$SERVER_ROOT/Example/logs/error.log" \
  "$ARTIFACT_DIR/logs/lshttpd.stderr" \
  "$ARTIFACT_DIR/logs/client.stderr" \
  >"$ARTIFACT_DIR/logs/migration-grep.log" || true

{
  cat "$ARTIFACT_DIR/source.env"
  print_kv validation "pending"
  print_kv version_exit "$VERSION_EXIT"
  print_kv config_test_exit "$CONFIG_TEST_EXIT"
  print_kv client_exit "$CLIENT_EXIT"
  print_kv client_response_bytes "$CLIENT_RESPONSE_BYTES"
  print_kv access_get_file_count "$ACCESS_GET_FILE_COUNT"
  print_kv server_path_challenge_count "$SERVER_PATH_CHALLENGE_COUNT"
  print_kv server_path_response_count "$SERVER_PATH_RESPONSE_COUNT"
  print_kv server_migration_count "$SERVER_MIGRATION_COUNT"
  print_kv client_path_validated_count "$CLIENT_PATH_VALIDATED_COUNT"
  print_kv client_path_failed_count "$CLIENT_PATH_FAILED_COUNT"
} >"$ARTIFACT_DIR/result.env"

VALIDATION="ok"
if [[ "$CLIENT_EXIT" != "0" ]]; then
  VALIDATION="failed_client_exit"
elif [[ "$CLIENT_RESPONSE_BYTES" != "$PAYLOAD_BYTES" ]]; then
  VALIDATION="failed_response_size"
elif [[ "$ACCESS_GET_FILE_COUNT" -lt 1 ]]; then
  VALIDATION="failed_missing_access_log"
elif [[ "$SERVER_PATH_CHALLENGE_COUNT" -lt 1 || "$SERVER_PATH_RESPONSE_COUNT" -lt 1 ]]; then
  VALIDATION="failed_missing_server_path_frames"
elif [[ "$CLIENT_PATH_VALIDATED_COUNT" -lt 1 ]]; then
  VALIDATION="failed_missing_client_validation"
fi

python3 - "$ARTIFACT_DIR/result.env" "$VALIDATION" <<'PY'
import sys
path, validation = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
text = text.replace("validation=pending\n", f"validation={validation}\n")
open(path, "w", encoding="utf-8").write(text)
PY

cat "$ARTIFACT_DIR/result.env"

if [[ "$VALIDATION" != "ok" ]]; then
  echo "OpenLiteSpeed active migration demo validation failed: $VALIDATION" >&2
  exit 1
fi
