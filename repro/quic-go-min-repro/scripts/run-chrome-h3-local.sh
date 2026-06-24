#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPRO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPRO_DIR"

CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
RUN_ID="${RUN_ID:-chrome-h3-local-$(date -u +%Y%m%dT%H%M%SZ)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-artifacts/${RUN_ID}}"
ADDR="${ADDR:-127.0.0.1:4443}"
REQUEST_PATH="${REQUEST_PATH:-/download?bytes=128&label=chrome-baseline}"
TIMEOUT="${TIMEOUT:-60s}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-45}"

mkdir -p "$ARTIFACT_DIR/chrome" "$ARTIFACT_DIR/certs" "$ARTIFACT_DIR/logs" "$ARTIFACT_DIR/results" "$ARTIFACT_DIR/qlog" "$ARTIFACT_DIR/keylog"

CERT_FILE="$ARTIFACT_DIR/certs/server.pem"
KEY_FILE="$ARTIFACT_DIR/certs/server-key.pem"
SPKI_FILE="$ARTIFACT_DIR/certs/server.spki"

if [[ ! -x "$CHROME_BIN" ]]; then
  echo "Chrome binary not found or not executable: $CHROME_BIN" >&2
  exit 2
fi

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -days 1 \
  -subj "/CN=quic-cm-repro.local" \
  -addext "subjectAltName=DNS:localhost,DNS:quic-cm-repro.local,IP:127.0.0.1,IP:::1" \
  >/dev/null 2>&1

SPKI_HASH="$(
  openssl x509 -pubkey -noout -in "$CERT_FILE" |
    openssl pkey -pubin -outform der |
    openssl dgst -sha256 -binary |
    base64
)"
printf '%s\n' "$SPKI_HASH" >"$SPKI_FILE"

QUIC_CM_CERT_FILE="$CERT_FILE" \
QUIC_CM_KEY_FILE="$KEY_FILE" \
EXPECTED_REQUESTS=1 \
ARTIFACT_DIR="$ARTIFACT_DIR" \
LISTEN_ADDR="$ADDR" \
TIMEOUT="$TIMEOUT" \
./scripts/run-h3-server.sh >"$ARTIFACT_DIR/logs/server-wrapper.log" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

sleep 2

CHROME_EXIT=0
python3 - "$CHROME_BIN" "$ARTIFACT_DIR" "$ADDR" "$REQUEST_PATH" "$SPKI_HASH" "$CHROME_TIMEOUT_SECONDS" <<'PY' || CHROME_EXIT=$?
import pathlib
import subprocess
import sys

chrome_bin, artifact_dir, addr, request_path, spki_hash, timeout_s = sys.argv[1:]
artifact = pathlib.Path(artifact_dir)
url = f"https://{addr}{request_path}"
cmd = [
    chrome_bin,
    "--headless=new",
    "--no-first-run",
    "--disable-gpu",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-sync",
    "--enable-quic",
    f"--origin-to-force-quic-on={addr}",
    f"--ignore-certificate-errors-spki-list={spki_hash}",
    f"--user-data-dir={artifact / 'chrome' / 'profile'}",
    f"--log-net-log={artifact / 'chrome' / 'netlog.json'}",
    "--net-log-capture-mode=Everything",
    "--dump-dom",
    url,
]
with (artifact / "chrome" / "dump-dom.txt").open("wb") as out, (artifact / "chrome" / "chrome.stderr.log").open("wb") as err:
    try:
        subprocess.run(cmd, stdout=out, stderr=err, timeout=int(timeout_s), check=True)
    except subprocess.TimeoutExpired:
        raise SystemExit(124)
PY

SERVER_EXIT=0
wait "$SERVER_PID" || SERVER_EXIT=$?
trap - EXIT

python3 - "$ARTIFACT_DIR" "$CHROME_EXIT" "$SERVER_EXIT" <<'PY'
import json
import pathlib
import sys

base = pathlib.Path(sys.argv[1])
chrome_exit = int(sys.argv[2])
server_exit = int(sys.argv[3])
server_path = base / "results" / "server.json"
server = json.loads(server_path.read_text()) if server_path.exists() else {}
netlog_path = base / "chrome" / "netlog.json"
netlog = netlog_path.read_text(errors="ignore") if netlog_path.exists() else ""
dump_path = base / "chrome" / "dump-dom.txt"
dump = dump_path.read_text(errors="ignore") if dump_path.exists() else ""
qlog_text = ""
for path in (base / "qlog").glob("*"):
    if path.is_file():
        qlog_text += path.read_text(errors="ignore")
requests = server.get("requests") or []
netlog_has_quic_session = "QUIC_SESSION" in netlog
qlog_has_h3 = "http3:frame" in qlog_text
request_reached_server = server.get("ok") is True and len(requests) >= 1
passed = request_reached_server and netlog_has_quic_session and qlog_has_h3
summary = {
    "status": "PASS" if passed else "FAIL",
    "artifact_dir": str(base),
    "chrome_exit": chrome_exit,
    "chrome_completed_cleanly": chrome_exit == 0,
    "chrome_timed_out_after_request": chrome_exit == 124 and request_reached_server,
    "server_exit": server_exit,
    "server_ok": server.get("ok"),
    "server_error": server.get("error"),
    "server_request_count": len(requests),
    "server_remote_addr": requests[0].get("remote_addr") if requests else None,
    "netlog_has_forced_origin": "origin-to-force-quic" in netlog or "127.0.0.1" in netlog,
    "netlog_has_quic_session": netlog_has_quic_session,
    "qlog_has_h3": qlog_has_h3,
    "qlog_has_path_validation": "path_challenge" in qlog_text or "path_response" in qlog_text,
    "dump_dom_bytes": len(dump),
    "dump_has_chrome_error": "ERR_" in dump,
}
(base / "results" / "chrome-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if summary["status"] != "PASS":
    raise SystemExit(1)
PY
