#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

require_command aws
require_command curl
require_command go
require_command ssh
require_command scp
require_command tar

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
AWS_PROFILE="${AWS_PROFILE:-}"
RESOURCE_PREFIX="${RESOURCE_PREFIX:-quic-cm-lab}"
PORT="${PORT:-4242}"
NLB_PROTOCOL="${NLB_PROTOCOL:-QUIC}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-65536}"
WORKLOAD="${WORKLOAD:-transport}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-10s}"
TIMEOUT="${TIMEOUT:-90s}"
POST_SEND_WAIT="${POST_SEND_WAIT:-3s}"
MIGRATION_AT_BYTES="${MIGRATION_AT_BYTES:-0}"
CHUNK_BYTES="${CHUNK_BYTES:-16384}"
CHUNK_DELAY="${CHUNK_DELAY:-2ms}"
CLIENT_START_DELAY_SECONDS="${CLIENT_START_DELAY_SECONDS:-5}"
SERVER_TIMEOUT="${SERVER_TIMEOUT:-600s}"
COMPLETION_GRACE="${COMPLETION_GRACE:-500ms}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t4g.micro}"
TARGET_A_SERVER_ID="${TARGET_A_SERVER_ID:-0xa1b2c3d4e5f65890}"
TARGET_B_SERVER_ID="${TARGET_B_SERVER_ID:-0xa1b2c3d4e5f65999}"
SERVER_A_CID_SERVER_ID="${SERVER_A_CID_SERVER_ID:-$TARGET_A_SERVER_ID}"
SERVER_B_CID_SERVER_ID="${SERVER_B_CID_SERVER_ID:-$TARGET_B_SERVER_ID}"
EXPECTED_OUTCOME="${EXPECTED_OUTCOME:-positive}"
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SHORT_STAMP="$(date -u +%Y%m%d%H%M%S)"
RUN_ID="${RUN_ID:-aws-nlb-quic-dp-$RUN_STAMP}"
RUN_DIR="$PROJECT_ROOT/harness/results/$RUN_ID"
RESULT_DIR="$RUN_DIR/results"
LOG_DIR="$RUN_DIR/logs"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

export AWS_REGION
export AWS_DEFAULT_REGION="$AWS_REGION"
if [[ -n "$AWS_PROFILE" ]]; then
  export AWS_PROFILE
fi

KEY_NAME="${RESOURCE_PREFIX}-${RUN_ID}-key"
KEY_PATH="$RUN_DIR/$KEY_NAME"
SG_NAME="${RESOURCE_PREFIX}-${RUN_ID}-sg"
LB_NAME="qcm-nlb-$SHORT_STAMP"
TG_NAME="qcm-q-$SHORT_STAMP"
TARGET_A_NAME="${RESOURCE_PREFIX}-${RUN_ID}-target-a"
TARGET_B_NAME="${RESOURCE_PREFIX}-${RUN_ID}-target-b"
REMOTE_DIR="/home/ec2-user/quic-go-min-repro"
REMOTE_PACKAGE="/home/ec2-user/quic-go-min-repro.tar.gz"
REMOTE_BOOTSTRAP="/home/ec2-user/ec2-bootstrap-go.sh"
REMOTE_HEALTH="/home/ec2-user/tcp-health.py"

LB_ARN=""
LISTENER_ARN=""
TG_ARN=""
SG_ID=""
INSTANCE_A=""
INSTANCE_B=""
CLEANUP_STATUS="not-started"
TARGETS_COLLECTED=0

case "$WORKLOAD" in
  transport|h3|h3-midflight-upload|h3-midflight-download)
    ;;
  *)
    echo "unsupported WORKLOAD=$WORKLOAD" >&2
    exit 2
    ;;
esac

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_DIR/run.log"
}

manifest_set() {
  printf '%s=%s\n' "$1" "$2" >>"$RESULT_DIR/manifest.env"
}

aws_json() {
  local name="$1"
  shift
  aws "$@" --output json | tee "$LOG_DIR/$name.json"
}

cleanup() {
  local exit_code=$?
  if [[ "${KEEP_AWS_RESOURCES:-0}" == "1" ]]; then
    CLEANUP_STATUS="skipped-keep-aws-resources"
    manifest_set "cleanup_status" "$CLEANUP_STATUS"
    log "cleanup skipped because KEEP_AWS_RESOURCES=1"
    exit "$exit_code"
  fi

  set +e
  log "cleanup start"

  if [[ "${TARGETS_COLLECTED:-0}" != "1" && -f "$KEY_PATH" && ( -n "${PUBLIC_IP_A:-}" || -n "${PUBLIC_IP_B:-}" ) ]]; then
    log "collect target artifacts before cleanup"
    collect_all_targets >/dev/null 2>&1 || true
  fi

  for ip in "${PUBLIC_IP_A:-}" "${PUBLIC_IP_B:-}"; do
    if [[ -n "$ip" && -f "$KEY_PATH" ]]; then
      ssh_quiet "$ip" "pkill -f 'go run ./cmd/' >/dev/null 2>&1 || true; pkill -f tcp-health.py >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
    fi
  done

  if [[ -n "$LISTENER_ARN" ]]; then
    aws elbv2 delete-listener --listener-arn "$LISTENER_ARN" >/dev/null 2>&1 || true
  fi
  if [[ -n "$LB_ARN" ]]; then
    aws elbv2 delete-load-balancer --load-balancer-arn "$LB_ARN" >/dev/null 2>&1 || true
    aws elbv2 wait load-balancers-deleted --load-balancer-arns "$LB_ARN" >/dev/null 2>&1 || true
  fi
  if [[ -n "$TG_ARN" ]]; then
    local deregister_targets=()
    if [[ -n "$INSTANCE_A" ]]; then
      deregister_targets+=(Id="$INSTANCE_A",Port="$PORT")
    fi
    if [[ -n "$INSTANCE_B" ]]; then
      deregister_targets+=(Id="$INSTANCE_B",Port="$PORT")
    fi
    if [[ "${#deregister_targets[@]}" -gt 0 ]]; then
      aws elbv2 deregister-targets --target-group-arn "$TG_ARN" --targets "${deregister_targets[@]}" >/dev/null 2>&1 || true
    fi
    aws elbv2 delete-target-group --target-group-arn "$TG_ARN" >/dev/null 2>&1 || true
  fi
  if [[ -n "$INSTANCE_A" || -n "$INSTANCE_B" ]]; then
    local terminate_instances=()
    if [[ -n "$INSTANCE_A" ]]; then
      terminate_instances+=("$INSTANCE_A")
    fi
    if [[ -n "$INSTANCE_B" ]]; then
      terminate_instances+=("$INSTANCE_B")
    fi
    aws ec2 terminate-instances --instance-ids "${terminate_instances[@]}" >/dev/null 2>&1 || true
    aws ec2 wait instance-terminated --instance-ids "${terminate_instances[@]}" >/dev/null 2>&1 || true
  fi
  if [[ -n "$SG_ID" ]]; then
    aws ec2 delete-security-group --group-id "$SG_ID" >/dev/null 2>&1 || true
  fi
  aws ec2 delete-key-pair --key-name "$KEY_NAME" >/dev/null 2>&1 || true
  rm -f "$KEY_PATH" "${KEY_PATH}.pub"

  CLEANUP_STATUS="deleted-listener-lb-tg-instances-sg-keypair"
  manifest_set "cleanup_status" "$CLEANUP_STATUS"
  log "cleanup done: $CLEANUP_STATUS"
  exit "$exit_code"
}
trap cleanup EXIT

ssh_quiet() {
  local ip="$1"
  shift
  ssh -i "$KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="$RUN_DIR/known_hosts" \
    -o ConnectTimeout=10 \
    "ec2-user@$ip" "$@"
}

scp_quiet() {
  scp -i "$KEY_PATH" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile="$RUN_DIR/known_hosts" \
    "$@"
}

wait_for_ssh() {
  local ip="$1"
  for _ in $(seq 1 60); do
    if ssh_quiet "$ip" "echo ssh-ok" >/dev/null 2>&1; then
      return 0
    fi
    sleep 5
  done
  echo "SSH did not become ready for $ip" >&2
  return 1
}

start_target() {
  local ip="$1"
  local target_name="$2"
  local server_id="$3"

  log "bootstrap target $target_name at $ip"
  scp_quiet "$PACKAGE_PATH" "ec2-user@$ip:$REMOTE_PACKAGE"
  scp_quiet "$PROJECT_ROOT/repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh" "ec2-user@$ip:$REMOTE_BOOTSTRAP"

  ssh_quiet "$ip" "bash $REMOTE_BOOTSTRAP" | tee "$LOG_DIR/bootstrap-$target_name.log"

  ssh_quiet "$ip" "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR && tar -xzf $REMOTE_PACKAGE -C $REMOTE_DIR"
  if (( PORT < 1024 )); then
    ssh_quiet "$ip" "sudo sysctl -w net.ipv4.ip_unprivileged_port_start=0" | tee "$LOG_DIR/unprivileged-port-$target_name.log"
  fi
  ssh_quiet "$ip" "cat > $REMOTE_HEALTH <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', $PORT))
s.listen(64)
while True:
    conn, addr = s.accept()
    conn.close()
PY
nohup python3 -u $REMOTE_HEALTH > /home/ec2-user/tcp-health.log 2>&1 & echo \$! > /home/ec2-user/tcp-health.pid"

  local server_script="./scripts/run-server.sh"
  local expected_requests=2
  if [[ "$WORKLOAD" == h3* ]]; then
    server_script="./scripts/run-h3-server.sh"
    if [[ "$WORKLOAD" != "h3" ]]; then
      expected_requests=1
    fi
  fi
  ssh_quiet "$ip" "cd $REMOTE_DIR && (ARTIFACT_DIR=artifacts/${target_name}-${RUN_ID} SERVER_ID=$server_id LISTEN_ADDR=0.0.0.0:$PORT TIMEOUT=$SERVER_TIMEOUT COMPLETION_GRACE=$COMPLETION_GRACE EXPECTED_REQUESTS=$expected_requests nohup $server_script > server-run.log 2>&1 & echo \$! > server.pid)"
  ssh_quiet "$ip" "sleep 5; cd $REMOTE_DIR; if ! kill -0 \$(cat server.pid) >/dev/null 2>&1; then echo 'QUIC server process is not running' >&2; tail -120 server-run.log >&2; exit 1; fi; echo quic-server-started" | tee "$LOG_DIR/server-start-$target_name.log"
}

collect_target() {
  local ip="$1"
  local target_name="$2"
  local out="$RUN_DIR/$target_name"
  mkdir -p "$out"

  ssh_quiet "$ip" "pkill -f tcp-health.py >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
  ssh_quiet "$ip" "cd /home/ec2-user && tar -czf ${target_name}.tgz quic-go-min-repro/artifacts quic-go-min-repro/server-run.log quic-go-min-repro/server.pid tcp-health.log tcp-health.pid 2>/dev/null || true" >/dev/null 2>&1 || true
  scp_quiet "ec2-user@$ip:/home/ec2-user/${target_name}.tgz" "$out/${target_name}.tgz" >/dev/null 2>&1 || true
  if [[ -f "$out/${target_name}.tgz" ]]; then
    tar -xzf "$out/${target_name}.tgz" -C "$out" || true
  fi
}

collect_all_targets() {
  if [[ "$TARGETS_COLLECTED" == "1" ]]; then
    return 0
  fi
  if [[ -n "${PUBLIC_IP_A:-}" ]]; then
    collect_target "$PUBLIC_IP_A" "target-a"
  fi
  if [[ -n "${PUBLIC_IP_B:-}" ]]; then
    collect_target "$PUBLIC_IP_B" "target-b"
  fi
  TARGETS_COLLECTED=1
}

cat >"$RESULT_DIR/manifest.env" <<EOF
run_id=$RUN_ID
started_at=$RUN_STAMP
aws_profile=${AWS_PROFILE:-default}
aws_region=$AWS_REGION
port=$PORT
nlb_protocol=$NLB_PROTOCOL
workload=$WORKLOAD
payload_bytes=$PAYLOAD_BYTES
probe_timeout=$PROBE_TIMEOUT
timeout=$TIMEOUT
post_send_wait=$POST_SEND_WAIT
migration_at_bytes=$MIGRATION_AT_BYTES
chunk_bytes=$CHUNK_BYTES
chunk_delay=$CHUNK_DELAY
client_start_delay_seconds=$CLIENT_START_DELAY_SECONDS
server_timeout=$SERVER_TIMEOUT
completion_grace=$COMPLETION_GRACE
target_a_server_id=$TARGET_A_SERVER_ID
target_b_server_id=$TARGET_B_SERVER_ID
server_a_cid_server_id=$SERVER_A_CID_SERVER_ID
server_b_cid_server_id=$SERVER_B_CID_SERVER_ID
expected_outcome=$EXPECTED_OUTCOME
EOF

log "AWS NLB QUIC data-plane run start: $RUN_ID"
log "NLB protocol=$NLB_PROTOCOL port=$PORT"
log "workload=$WORKLOAD"

"$SCRIPT_DIR/aws-preflight.sh" | tee "$LOG_DIR/aws-preflight.log"

CLIENT_PUBLIC_CIDR="${CLIENT_PUBLIC_CIDR:-}"
if [[ -z "$CLIENT_PUBLIC_CIDR" ]]; then
  CLIENT_PUBLIC_IP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
  CLIENT_PUBLIC_CIDR="$CLIENT_PUBLIC_IP/32"
fi
manifest_set "client_public_cidr" "$CLIENT_PUBLIC_CIDR"

VPC_ID="$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)"
if [[ "$VPC_ID" == "None" || -z "$VPC_ID" ]]; then
  echo "default VPC not found" >&2
  exit 1
fi
VPC_CIDR="$(aws ec2 describe-vpcs --vpc-ids "$VPC_ID" --query 'Vpcs[0].CidrBlock' --output text)"
mapfile -t SUBNETS < <(aws ec2 describe-subnets \
  --filters Name=vpc-id,Values="$VPC_ID" Name=default-for-az,Values=true \
  --query 'Subnets | sort_by(@,&AvailabilityZone)[].SubnetId' \
  --output text | tr '\t' '\n' | sed '/^$/d' | head -2)
if [[ "${#SUBNETS[@]}" -lt 2 ]]; then
  echo "need at least two default subnets in $VPC_ID" >&2
  exit 1
fi
SUBNET_A="${SUBNETS[0]}"
SUBNET_B="${SUBNETS[1]}"
AMI_ID="$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query 'Parameter.Value' --output text)"

manifest_set "vpc_id" "$VPC_ID"
manifest_set "vpc_cidr" "$VPC_CIDR"
manifest_set "subnet_a" "$SUBNET_A"
manifest_set "subnet_b" "$SUBNET_B"
manifest_set "ami_id" "$AMI_ID"
manifest_set "instance_type" "$INSTANCE_TYPE"

log "package quic-go repro"
PACKAGE_LOG="$LOG_DIR/package.log"
"$SCRIPT_DIR/package-quic-go-ec2.sh" | tee "$PACKAGE_LOG"
PACKAGE_PATH="$(awk -F= '$1=="package_path"{print $2}' "$PACKAGE_LOG" | tail -1)"
if [[ -z "$PACKAGE_PATH" || ! -f "$PACKAGE_PATH" ]]; then
  echo "package path not found" >&2
  exit 1
fi
manifest_set "package_path" "$PACKAGE_PATH"

log "create SSH key pair"
ssh-keygen -t ed25519 -N "" -C "$KEY_NAME" -f "$KEY_PATH" >/dev/null
chmod 600 "$KEY_PATH"
aws ec2 import-key-pair --key-name "$KEY_NAME" --public-key-material "fileb://${KEY_PATH}.pub" >"$LOG_DIR/import-key-pair.json"
aws ec2 create-tags --resources "$KEY_NAME" --tags Key=Project,Value=quic-connection-migration Key=Owner,Value=manwook Key=Purpose,Value=research Key=RunId,Value="$RUN_ID" >/dev/null 2>&1 || true
manifest_set "key_name" "$KEY_NAME"

log "create target security group"
SG_ID="$(aws ec2 create-security-group --group-name "$SG_NAME" --description "QUIC NLB data-plane $RUN_ID" --vpc-id "$VPC_ID" --query GroupId --output text)"
aws ec2 create-tags --resources "$SG_ID" --tags Key=Name,Value="$SG_NAME" Key=Project,Value=quic-connection-migration Key=Owner,Value=manwook Key=Purpose,Value=research Key=RunId,Value="$RUN_ID"
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$CLIENT_PUBLIC_CIDR" >/dev/null
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol udp --port "$PORT" --cidr "$CLIENT_PUBLIC_CIDR" >/dev/null
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol udp --port "$PORT" --cidr "$VPC_CIDR" >/dev/null
aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port "$PORT" --cidr "$VPC_CIDR" >/dev/null
manifest_set "sg_id" "$SG_ID"
aws ec2 describe-security-groups --group-ids "$SG_ID" >"$LOG_DIR/security-group.json"

log "launch EC2 target A/B"
INSTANCE_A="$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_A" \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TARGET_A_NAME},{Key=Project,Value=quic-connection-migration},{Key=Owner,Value=manwook},{Key=Purpose,Value=research},{Key=RunId,Value=$RUN_ID},{Key=Target,Value=A}]" \
  --query 'Instances[0].InstanceId' --output text)"
INSTANCE_B="$(aws ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type "$INSTANCE_TYPE" \
  --key-name "$KEY_NAME" \
  --security-group-ids "$SG_ID" \
  --subnet-id "$SUBNET_B" \
  --associate-public-ip-address \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$TARGET_B_NAME},{Key=Project,Value=quic-connection-migration},{Key=Owner,Value=manwook},{Key=Purpose,Value=research},{Key=RunId,Value=$RUN_ID},{Key=Target,Value=B}]" \
  --query 'Instances[0].InstanceId' --output text)"
manifest_set "instance_a" "$INSTANCE_A"
manifest_set "instance_b" "$INSTANCE_B"
aws ec2 wait instance-running --instance-ids "$INSTANCE_A" "$INSTANCE_B"

PUBLIC_IP_A="$(aws ec2 describe-instances --instance-ids "$INSTANCE_A" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
PUBLIC_IP_B="$(aws ec2 describe-instances --instance-ids "$INSTANCE_B" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"
PRIVATE_IP_A="$(aws ec2 describe-instances --instance-ids "$INSTANCE_A" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)"
PRIVATE_IP_B="$(aws ec2 describe-instances --instance-ids "$INSTANCE_B" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)"
manifest_set "public_ip_a" "$PUBLIC_IP_A"
manifest_set "public_ip_b" "$PUBLIC_IP_B"
manifest_set "private_ip_a" "$PRIVATE_IP_A"
manifest_set "private_ip_b" "$PRIVATE_IP_B"
aws ec2 describe-instances --instance-ids "$INSTANCE_A" "$INSTANCE_B" >"$LOG_DIR/instances.json"

log "wait SSH"
wait_for_ssh "$PUBLIC_IP_A"
wait_for_ssh "$PUBLIC_IP_B"

start_target "$PUBLIC_IP_A" "target-a" "$SERVER_A_CID_SERVER_ID"
start_target "$PUBLIC_IP_B" "target-b" "$SERVER_B_CID_SERVER_ID"

log "create target group"
TG_ARN="$(aws elbv2 create-target-group \
  --name "$TG_NAME" \
  --protocol "$NLB_PROTOCOL" \
  --port "$PORT" \
  --vpc-id "$VPC_ID" \
  --target-type instance \
  --health-check-protocol TCP \
  --health-check-port "$PORT" \
  --health-check-interval-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 2 \
  --tags Key=Project,Value=quic-connection-migration Key=Owner,Value=manwook Key=Purpose,Value=research Key=RunId,Value="$RUN_ID" \
  --query 'TargetGroups[0].TargetGroupArn' --output text)"
manifest_set "target_group_arn" "$TG_ARN"

log "create NLB"
LB_JSON="$LOG_DIR/create-load-balancer.json"
aws elbv2 create-load-balancer \
  --name "$LB_NAME" \
  --type network \
  --scheme internet-facing \
  --ip-address-type ipv4 \
  --subnets "$SUBNET_A" "$SUBNET_B" \
  --tags Key=Project,Value=quic-connection-migration Key=Owner,Value=manwook Key=Purpose,Value=research Key=RunId,Value="$RUN_ID" \
  --output json | tee "$LB_JSON"
LB_ARN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["LoadBalancers"][0]["LoadBalancerArn"])' "$LB_JSON")"
LB_DNS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["LoadBalancers"][0]["DNSName"])' "$LB_JSON")"
manifest_set "load_balancer_arn" "$LB_ARN"
manifest_set "load_balancer_dns" "$LB_DNS"
aws elbv2 wait load-balancer-available --load-balancer-arns "$LB_ARN"

log "create QUIC listener"
LISTENER_ARN="$(aws elbv2 create-listener \
  --load-balancer-arn "$LB_ARN" \
  --protocol "$NLB_PROTOCOL" \
  --port "$PORT" \
  --default-actions Type=forward,TargetGroupArn="$TG_ARN" \
  --query 'Listeners[0].ListenerArn' --output text)"
manifest_set "listener_arn" "$LISTENER_ARN"

log "register targets with QuicServerId"
aws elbv2 register-targets \
  --target-group-arn "$TG_ARN" \
  --targets \
    Id="$INSTANCE_A",Port="$PORT",QuicServerId="$TARGET_A_SERVER_ID" \
    Id="$INSTANCE_B",Port="$PORT",QuicServerId="$TARGET_B_SERVER_ID"

log "wait target health"
for i in $(seq 1 36); do
  aws elbv2 describe-target-health --target-group-arn "$TG_ARN" >"$LOG_DIR/target-health-$i.json"
  healthy_count="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(sum(1 for x in d["TargetHealthDescriptions"] if x["TargetHealth"]["State"]=="healthy"))' "$LOG_DIR/target-health-$i.json")"
  log "target health attempt $i: healthy=$healthy_count/2"
  if [[ "$healthy_count" == "2" ]]; then
    break
  fi
  sleep 10
done
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" >"$LOG_DIR/target-health-final.json"

log "run migration client through NLB $LB_DNS:$PORT"
if (( CLIENT_START_DELAY_SECONDS > 0 )); then
  log "wait ${CLIENT_START_DELAY_SECONDS}s before client start"
  sleep "$CLIENT_START_DELAY_SECONDS"
fi
CLIENT_ARTIFACT="$RUN_DIR/client"
CLIENT_EXIT=0
CLIENT_SCRIPT="$PROJECT_ROOT/repro/quic-go-min-repro/scripts/run-ec2-client.sh"
CLIENT_MODE="upload-download"
if [[ "$WORKLOAD" == h3* ]]; then
  CLIENT_SCRIPT="$PROJECT_ROOT/repro/quic-go-min-repro/scripts/run-h3-client.sh"
  case "$WORKLOAD" in
    h3)
      CLIENT_MODE="upload-download"
      ;;
    h3-midflight-upload)
      CLIENT_MODE="midflight-upload"
      ;;
    h3-midflight-download)
      CLIENT_MODE="midflight-download"
      ;;
  esac
fi
SERVER_ADDR="$LB_DNS:$PORT" \
  PAYLOAD_BYTES="$PAYLOAD_BYTES" \
  PROBE_TIMEOUT="$PROBE_TIMEOUT" \
  TIMEOUT="$TIMEOUT" \
  POST_SEND_WAIT="$POST_SEND_WAIT" \
  MODE="$CLIENT_MODE" \
  MIGRATION_AT_BYTES="$MIGRATION_AT_BYTES" \
  CHUNK_BYTES="$CHUNK_BYTES" \
  CHUNK_DELAY="$CHUNK_DELAY" \
  ARTIFACT_DIR="$CLIENT_ARTIFACT" \
  "$CLIENT_SCRIPT" "$LB_DNS:$PORT" | tee "$LOG_DIR/client-run.log" || CLIENT_EXIT=$?
manifest_set "client_exit_code" "$CLIENT_EXIT"
log "client exit code: $CLIENT_EXIT"

sleep 8
collect_all_targets

log "write summary"
EXPECTED_OUTCOME="$EXPECTED_OUTCOME" WORKLOAD="$WORKLOAD" python3 - "$RUN_DIR" <<'PY'
import json
import os
import pathlib
import sys

run = pathlib.Path(sys.argv[1])
expected_outcome = os.environ.get("EXPECTED_OUTCOME", "positive")
workload = os.environ.get("WORKLOAD", "transport")
client_path = run / "client" / "results" / "client.json"
client = json.loads(client_path.read_text()) if client_path.exists() else {}
servers = []
for target in ("target-a", "target-b"):
    for path in (run / target).glob("**/results/server.json"):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            data = {"ok": False, "error": str(exc)}
        data["_target"] = target
        data["_path"] = str(path)
        servers.append(data)

successful_servers = [s for s in servers if s.get("ok") is True]
if workload == "h3":
    same_target_success = len(successful_servers) == 1 and len(successful_servers[0].get("requests", [])) == 2
elif workload in ("h3-midflight-upload", "h3-midflight-download"):
    same_target_success = len(successful_servers) == 1 and len(successful_servers[0].get("requests", [])) == 1
else:
    same_target_success = len(successful_servers) == 1 and len(successful_servers[0].get("received", [])) == 2
positive_pass = client.get("ok") is True and same_target_success
if expected_outcome == "client-failure":
    status = "PASS_NEGATIVE_CONTROL" if client.get("ok") is not True else "FAIL_UNEXPECTED_PASS"
else:
    status = "PASS" if positive_pass else "FAIL_CLASSIFIED"
summary = {
    "status": status,
    "expected_outcome": expected_outcome,
    "workload": workload,
    "client_ok": client.get("ok"),
    "client_socket_a": client.get("socket_a_local_addr"),
    "client_socket_b": client.get("socket_b_local_addr"),
    "client_local_addr_changed_to_socket_b": client.get("local_addr_changed_to_socket_b"),
    "server_success_count": len(successful_servers),
    "successful_target": successful_servers[0].get("_target") if successful_servers else None,
    "servers": servers,
}
(run / "results" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
PY

log "AWS NLB QUIC data-plane run complete"
if [[ "$EXPECTED_OUTCOME" == "client-failure" ]]; then
  if [[ "$CLIENT_EXIT" != "0" ]]; then
    exit 0
  fi
  exit 1
fi
exit "$CLIENT_EXIT"
