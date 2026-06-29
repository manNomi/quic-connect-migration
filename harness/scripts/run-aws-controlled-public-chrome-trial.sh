#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env
require_command ssh
require_command scp
require_command python3

STATE_FILE="${AWS_ORIGIN_STATE_FILE:-$HARNESS_DIR/results/aws-origin-20260629/state.env}"
CONFIG_FILE="${CONTROLLED_PUBLIC_CONFIG:-$HARNESS_DIR/config/controlled-public-origin.env}"
EXPLICIT_BASELINE_SUMMARY_SET=0
EXPLICIT_BASELINE_SUMMARY=""
if [[ ${CONTROLLED_PUBLIC_BASELINE_SUMMARY+x} ]]; then
  EXPLICIT_BASELINE_SUMMARY_SET=1
  EXPLICIT_BASELINE_SUMMARY="$CONTROLLED_PUBLIC_BASELINE_SUMMARY"
fi
EXPLICIT_TLS_CERT_FILE_SET=0
EXPLICIT_TLS_CERT_FILE=""
if [[ ${TLS_CERT_FILE+x} ]]; then
  EXPLICIT_TLS_CERT_FILE_SET=1
  EXPLICIT_TLS_CERT_FILE="$TLS_CERT_FILE"
fi
EXPLICIT_TLS_KEY_FILE_SET=0
EXPLICIT_TLS_KEY_FILE=""
if [[ ${TLS_KEY_FILE+x} ]]; then
  EXPLICIT_TLS_KEY_FILE_SET=1
  EXPLICIT_TLS_KEY_FILE="$TLS_KEY_FILE"
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "missing AWS origin state file: $STATE_FILE" >&2
  exit 2
fi
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "missing controlled public config file: $CONFIG_FILE" >&2
  exit 2
fi

load_env_if_present "$STATE_FILE"
load_env_if_present "$CONFIG_FILE"
if [[ "$EXPLICIT_BASELINE_SUMMARY_SET" == "1" ]]; then
  CONTROLLED_PUBLIC_BASELINE_SUMMARY="$EXPLICIT_BASELINE_SUMMARY"
fi

REPRO_DIR="$PROJECT_ROOT/repro/quic-go-min-repro"
MODE="${MODE:-network-change}"
VARIANT="${VARIANT:-noheartbeat}"
TRIAL_ID="${TRIAL_ID:-controlled-public-chrome-downlink-${VARIANT}-${MODE}-$(date -u +%Y%m%dT%H%M%SZ)}"
UNIT_NAME="${UNIT_NAME:-quic-cm-repeat}"
REMOTE_DIR="${REMOTE_DIR:-/home/ec2-user/quic-go-min-repro}"
REMOTE_ARTIFACT_DIR="artifacts/$TRIAL_ID"
LOCAL_ARTIFACT_REL="repro/quic-go-min-repro/artifacts/$TRIAL_ID"
LOCAL_SERVER_ARTIFACT_REL="repro/quic-go-min-repro/artifacts/${TRIAL_ID}-server"
LOCAL_ARTIFACT_DIR="$PROJECT_ROOT/$LOCAL_ARTIFACT_REL"
LOCAL_SERVER_ARTIFACT_DIR="$PROJECT_ROOT/$LOCAL_SERVER_ARTIFACT_REL"
PUBLIC_HOST="${CANDIDATE_HOST:-${PUBLIC_ORIGIN_HOST:-}}"

if [[ -z "$PUBLIC_HOST" ]]; then
  echo "missing public host in state/config" >&2
  exit 2
fi

BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-https://$PUBLIC_HOST/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}"
case "$VARIANT" in
  noheartbeat)
    TARGET_URL="${TARGET_URL:-${PUBLIC_ORIGIN_NETWORK_CHANGE_URL:-${PUBLIC_ORIGIN_NOCHANGE_URL:-https://$PUBLIC_HOST/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat}}}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-5}"
    ;;
  heartbeat)
    TARGET_URL="${TARGET_URL:-https://$PUBLIC_HOST/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat}"
    EXPECTED_REQUESTS="${EXPECTED_REQUESTS:-6}"
    ;;
  *)
    echo "unsupported VARIANT=$VARIANT; expected noheartbeat or heartbeat" >&2
    exit 2
    ;;
esac

if [[ "$MODE" == "network-change" ]]; then
  RUNNER="$REPRO_DIR/scripts/run-controlled-public-h3-network-change.sh"
  NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:-networksetup -setairportpower 'en0' off}"
  NETWORK_CHANGE_AFTER_SECONDS="${NETWORK_CHANGE_AFTER_SECONDS:-3}"
  NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT="${NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT:-10}"
  NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS="${NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS:-1}"
  REQUIRE_CONTROLLED_PUBLIC_BASELINE="${REQUIRE_CONTROLLED_PUBLIC_BASELINE:-1}"
  COMPLETION_GRACE="${COMPLETION_GRACE:-45s}"
elif [[ "$MODE" == "nochange" ]]; then
  RUNNER="$REPRO_DIR/scripts/run-controlled-public-h3-browser-baseline.sh"
  REQUIRE_CONTROLLED_PUBLIC_BASELINE=0
  COMPLETION_GRACE="${COMPLETION_GRACE:-25s}"
else
  echo "unsupported MODE=$MODE; expected network-change or nochange" >&2
  exit 2
fi

if [[ "$EXPLICIT_TLS_CERT_FILE_SET" == "1" ]]; then
  TLS_CERT_FILE="$EXPLICIT_TLS_CERT_FILE"
else
  TLS_CERT_FILE="/etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem"
fi
if [[ "$EXPLICIT_TLS_KEY_FILE_SET" == "1" ]]; then
  TLS_KEY_FILE="$EXPLICIT_TLS_KEY_FILE"
else
  TLS_KEY_FILE="/etc/letsencrypt/live/$PUBLIC_HOST/privkey.pem"
fi
SSH_TARGET="${SSH_USER:-ec2-user}@${PUBLIC_DNS:?missing PUBLIC_DNS in state}"
SSH_KEY="${SSH_KEY:?missing SSH_KEY in state}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new -i "$SSH_KEY")
TIMEOUT="${TIMEOUT:-240s}"
SERVER_JSON_WAIT_SECONDS="${SERVER_JSON_WAIT_SECONDS:-75}"
CHROME_RUNNER="${CHROME_RUNNER:-cdp}"
CHROME_HOLD_SECONDS="${CHROME_HOLD_SECONDS:-28}"
CHROME_TIMEOUT_SECONDS="${CHROME_TIMEOUT_SECONDS:-50}"
CHROME_NET_LOG_CAPTURE_MODE="${CHROME_NET_LOG_CAPTURE_MODE:-Default}"
RESTORE_WIFI_CMD="${RESTORE_WIFI_CMD:-networksetup -setairportpower en0 on}"

if [[ "$MODE" == "network-change" && "$REQUIRE_CONTROLLED_PUBLIC_BASELINE" == "1" ]]; then
  if [[ -z "${CONTROLLED_PUBLIC_BASELINE_SUMMARY:-}" || ! -f "$CONTROLLED_PUBLIC_BASELINE_SUMMARY" ]]; then
    echo "set CONTROLLED_PUBLIC_BASELINE_SUMMARY to a local PASS baseline summary" >&2
    exit 2
  fi
fi

echo "== AWS controlled public Chrome trial =="
print_kv "trial_id" "$TRIAL_ID"
print_kv "mode" "$MODE"
print_kv "variant" "$VARIANT"
print_kv "expected_requests" "$EXPECTED_REQUESTS"
print_kv "local_artifact_dir" "$LOCAL_ARTIFACT_DIR"
print_kv "local_server_artifact_dir" "$LOCAL_SERVER_ARTIFACT_DIR"

rm -rf "$LOCAL_ARTIFACT_DIR" "$LOCAL_SERVER_ARTIFACT_DIR"

ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
  "TRIAL_ID=$(printf '%q' "$TRIAL_ID") PUBLIC_HOST=$(printf '%q' "$PUBLIC_HOST") TLS_CERT_FILE=$(printf '%q' "$TLS_CERT_FILE") TLS_KEY_FILE=$(printf '%q' "$TLS_KEY_FILE") EXPECTED_REQUESTS=$(printf '%q' "$EXPECTED_REQUESTS") TIMEOUT=$(printf '%q' "$TIMEOUT") COMPLETION_GRACE=$(printf '%q' "$COMPLETION_GRACE") UNIT_NAME=$(printf '%q' "$UNIT_NAME") REMOTE_DIR=$(printf '%q' "$REMOTE_DIR") bash -s" <<'REMOTE'
set -euo pipefail
sudo systemctl stop "$UNIT_NAME.service" 2>/dev/null || true
sudo rm -rf "$REMOTE_DIR/artifacts/$TRIAL_ID"
sudo systemd-run \
  --unit="$UNIT_NAME" \
  --collect \
  --property=WorkingDirectory="$REMOTE_DIR" \
  --setenv=HOME=/root \
  --setenv=PATH=/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin \
  --setenv=GOCACHE=/root/.cache/go-build \
  --setenv=GOMODCACHE=/root/go/pkg/mod \
  --setenv=RUN_ID="$TRIAL_ID" \
  --setenv=ARTIFACT_DIR="artifacts/$TRIAL_ID" \
  --setenv=PUBLIC_ORIGIN_HOST="$PUBLIC_HOST" \
  --setenv=PUBLIC_ORIGIN_PORT=443 \
  --setenv=TLS_CERT_FILE="$TLS_CERT_FILE" \
  --setenv=TLS_KEY_FILE="$TLS_KEY_FILE" \
  --setenv=LISTEN_ADDR=0.0.0.0:443 \
  --setenv=TCP_ADDR=0.0.0.0:443 \
  --setenv=ALT_SVC='h3=":443"; ma=60' \
  --setenv=EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
  --setenv=TIMEOUT="$TIMEOUT" \
  --setenv=COMPLETION_GRACE="$COMPLETION_GRACE" \
  --setenv=MIN_ARTIFACT_FREE_GIB=7 \
  "$REMOTE_DIR/scripts/run-controlled-public-h3-server.sh"
sleep 3
sudo systemctl is-active "$UNIT_NAME.service" || true
REMOTE

RUN_EXIT=0
set +e
if [[ "$MODE" == "network-change" ]]; then
  (
    cd "$REPRO_DIR"
    RUN_ID="$TRIAL_ID" \
      ARTIFACT_DIR="artifacts/$TRIAL_ID" \
      CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="artifacts/${TRIAL_ID}-server" \
      CONTROLLED_PUBLIC_BASELINE_SUMMARY="../../$CONTROLLED_PUBLIC_BASELINE_SUMMARY" \
      PUBLIC_ORIGIN_URL="$TARGET_URL" \
      PUBLIC_ORIGIN_BOOTSTRAP_URL="$BOOTSTRAP_URL" \
      CONTROLLED_PUBLIC_EXPECTED_REQUESTS="$EXPECTED_REQUESTS" \
      REQUIRE_H3_ALT_SVC=1 \
      REQUIRE_CONTROLLED_PUBLIC_BASELINE="$REQUIRE_CONTROLLED_PUBLIC_BASELINE" \
      CHROME_RUNNER="$CHROME_RUNNER" \
      CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
      CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
      CHROME_NET_LOG_CAPTURE_MODE="$CHROME_NET_LOG_CAPTURE_MODE" \
      NETWORK_CHANGE_AFTER_SECONDS="$NETWORK_CHANGE_AFTER_SECONDS" \
      NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT="$NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT" \
      NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS="$NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS" \
      NETWORK_CHANGE_CMD="$NETWORK_CHANGE_CMD" \
      "$RUNNER"
  )
  RUN_EXIT=$?
  $RESTORE_WIFI_CMD || true
  sleep 4
else
  (
    cd "$REPRO_DIR"
    RUN_ID="$TRIAL_ID" \
      ARTIFACT_DIR="artifacts/$TRIAL_ID" \
      PUBLIC_ORIGIN_URL="$BOOTSTRAP_URL" \
      PUBLIC_ORIGIN_BOOTSTRAP_URL="$BOOTSTRAP_URL" \
      SECOND_URL="$TARGET_URL" \
      REQUIRE_H3_ALT_SVC=1 \
      RUN_CONTROLLED_PUBLIC_CLASSIFIER=0 \
      CHROME_RUNNER="$CHROME_RUNNER" \
      CHROME_HOLD_SECONDS="$CHROME_HOLD_SECONDS" \
      CHROME_TIMEOUT_SECONDS="$CHROME_TIMEOUT_SECONDS" \
      CHROME_NET_LOG_CAPTURE_MODE="$CHROME_NET_LOG_CAPTURE_MODE" \
      "$RUNNER"
  )
  RUN_EXIT=$?
fi
set -e

route -n get default | awk '/interface:/{print "default_interface_after_run="$2}' || true

for _ in $(seq 1 "$SERVER_JSON_WAIT_SECONDS"); do
  ready="$(ssh "${SSH_OPTS[@]}" "$SSH_TARGET" "sudo test -f '$REMOTE_DIR/$REMOTE_ARTIFACT_DIR/results/server.json' && echo ready || true" 2>/dev/null || true)"
  if [[ "$ready" == "ready" ]]; then
    break
  fi
  sleep 1
done

ssh "${SSH_OPTS[@]}" "$SSH_TARGET" \
  "sudo systemctl is-active '$UNIT_NAME.service' 2>/dev/null || true; sudo test -f '$REMOTE_DIR/$REMOTE_ARTIFACT_DIR/results/server.json' && echo remote_server_json=ready || echo remote_server_json=missing"

rm -rf "$LOCAL_SERVER_ARTIFACT_DIR"
scp -q -r "${SSH_OPTS[@]}" "$SSH_TARGET:$REMOTE_DIR/$REMOTE_ARTIFACT_DIR" "$LOCAL_SERVER_ARTIFACT_DIR"

if [[ "$MODE" == "network-change" ]]; then
  python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_network_change.py" \
    "$LOCAL_ARTIFACT_DIR" \
    --server-artifact-dir "$LOCAL_SERVER_ARTIFACT_DIR" \
    --url "$TARGET_URL" \
    --chrome-exit "$RUN_EXIT" \
    --expected-requests "$EXPECTED_REQUESTS" \
    --output "$LOCAL_ARTIFACT_DIR/results/controlled-public-h3-network-change-summary.json" || true
else
  python3 "$PROJECT_ROOT/tools/classify_controlled_public_h3_baseline.py" \
    "$LOCAL_ARTIFACT_DIR" \
    --server-artifact-dir "$LOCAL_SERVER_ARTIFACT_DIR" \
    --browser-artifact-dir "$LOCAL_ARTIFACT_DIR" \
    --url "$TARGET_URL" \
    --expected-requests "$EXPECTED_REQUESTS" \
    --output "$LOCAL_ARTIFACT_DIR/results/controlled-public-h3-baseline-summary.json" || true
fi

python3 "$PROJECT_ROOT/tools/validate_final_handover_trial_artifact.py" \
  --trial-id "$TRIAL_ID" \
  --artifact-dir "$LOCAL_ARTIFACT_REL" \
  --output "$PROJECT_ROOT/docs/results/${TRIAL_ID}-validation.md" || true

python3 - "$LOCAL_ARTIFACT_DIR" "$MODE" "$RUN_EXIT" <<'PY'
import json
import sys
from pathlib import Path

artifact = Path(sys.argv[1])
mode = sys.argv[2]
run_exit = sys.argv[3]
name = "controlled-public-h3-network-change-summary.json" if mode == "network-change" else "controlled-public-h3-baseline-summary.json"
summary = json.loads((artifact / "results" / name).read_text(encoding="utf-8"))
app = summary.get("application") or {}
client_path = summary.get("client_path_change") or {}
server_requests = summary.get("server_requests") or {}
print("trial_summary=ok")
print(f"runner_exit={run_exit}")
for key in ["status", "classification", "browser_completed_cleanly", "server_qlog_has_path_validation"]:
    if key in summary:
        print(f"{key}={summary.get(key)}")
print(f"client_path_change={client_path.get('classification')}")
print(f"application_workload={app.get('workload')}")
print(f"application_complete={app.get('complete')}")
print(f"application_success={app.get('success')}")
print(f"server_request_count={server_requests.get('request_count')}")
print(f"target_h3_remote_addr_count={server_requests.get('target_h3_remote_addr_count')}")
PY

exit 0
