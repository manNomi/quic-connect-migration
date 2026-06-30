#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_lib.sh"

load_harness_env

AWS_REGION="${AWS_REGION:-ap-northeast-2}"
RESOURCE_PREFIX="${RESOURCE_PREFIX:-quic-cm-lab}"
PORT="${PORT:-4242}"
NLB_PROTOCOL="${NLB_PROTOCOL:-QUIC}"
PAYLOAD_BYTES="${PAYLOAD_BYTES:-4096}"
SERVER_TIMEOUT_SECS="${SERVER_TIMEOUT_SECS:-180}"
CLIENT_TIMEOUT_SECS="${CLIENT_TIMEOUT_SECS:-45}"
CLIENT_START_DELAY_SECONDS="${CLIENT_START_DELAY_SECONDS:-5}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t4g.micro}"
TARGET_A_SERVER_ID="${TARGET_A_SERVER_ID:-0xa1b2c3d4e5f65890}"
TARGET_B_SERVER_ID="${TARGET_B_SERVER_ID:-0xa1b2c3d4e5f65999}"
REQUIRE_LIVE="${REQUIRE_LIVE:-0}"
RUN_STAMP="$(timestamp_utc)"
SHORT_STAMP="$(date -u +%Y%m%d%H%M%S)"
RUN_ID="${RUN_ID:-aws-s2n-nlb-live-$RUN_STAMP}"
RUN_DIR="$PROJECT_ROOT/harness/results/$RUN_ID"
RESULT_DIR="$RUN_DIR/results"
LOG_DIR="$RUN_DIR/logs"
CRATE_DIR="$PROJECT_ROOT/experiments/s2n-quic-nlb-cid-provider"

mkdir -p "$RESULT_DIR" "$LOG_DIR"

export AWS_REGION
export AWS_DEFAULT_REGION="$AWS_REGION"
if [[ -n "${AWS_PROFILE:-}" ]]; then
  export AWS_PROFILE
fi

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_DIR/run.log"
}

manifest_set() {
  printf '%s=%s\n' "$1" "$2" >>"$RESULT_DIR/manifest.env"
}

json_value() {
  local path="$1"
  local expr="$2"
  python3 - "$path" "$expr" <<'PY'
import json
import sys

path, expr = sys.argv[1], sys.argv[2]
try:
    data = json.load(open(path, encoding="utf-8"))
except FileNotFoundError:
    print("")
    raise SystemExit(0)

value = data
for part in expr.split("."):
    if not part:
        continue
    if isinstance(value, dict):
        value = value.get(part, "")
    else:
        value = ""
        break
if isinstance(value, bool):
    print("yes" if value else "no")
elif value is None:
    print("")
else:
    print(value)
PY
}

command_found() {
  command -v "$1" >/dev/null 2>&1
}

write_blocked_result() {
  local reason="$1"
  local validation="${2:-blocked}"
  {
    print_kv "run_id" "$RUN_ID"
    print_kv "artifact_dir" "$RUN_DIR"
    print_kv "aws_region" "$AWS_REGION"
    print_kv "aws_identity_ok" "${AWS_IDENTITY_OK:-unknown}"
    print_kv "aws_identity_classification" "${AWS_IDENTITY_CLASSIFICATION:-unknown}"
    print_kv "aws_cli_found" "${AWS_CLI_FOUND:-unknown}"
    print_kv "cargo_found" "${CARGO_FOUND:-unknown}"
    print_kv "crate_ready" "${CRATE_READY:-unknown}"
    print_kv "server_binary_source_ready" "${SERVER_BINARY_SOURCE_READY:-unknown}"
    print_kv "client_binary_source_ready" "${CLIENT_BINARY_SOURCE_READY:-unknown}"
    print_kv "live_phase" "pre_resource_gate"
    print_kv "validation" "$validation"
    print_kv "blocked_reason" "$reason"
    print_kv "aws_identity_markdown" "$RESULT_DIR/aws-identity-readiness.md"
    print_kv "aws_identity_json" "$RESULT_DIR/aws-identity-readiness.json"
  } | tee "$RESULT_DIR/result.env"

  cat >"$RESULT_DIR/README.md" <<EOF
# AWS NLB + s2n-quic Live Data Plane Artifact

This artifact is public-safe. The runner stopped before creating AWS resources.

| field | value |
| --- | --- |
| run id | \`$RUN_ID\` |
| AWS identity ok | \`${AWS_IDENTITY_OK:-unknown}\` |
| AWS identity classification | \`${AWS_IDENTITY_CLASSIFICATION:-unknown}\` |
| crate ready | \`${CRATE_READY:-unknown}\` |
| server source ready | \`${SERVER_BINARY_SOURCE_READY:-unknown}\` |
| client source ready | \`${CLIENT_BINARY_SOURCE_READY:-unknown}\` |
| validation | \`$validation\` |
| blocked reason | \`$reason\` |

This result is not a live AWS NLB forwarding result and not an active migration result.
EOF
}

run_or_block() {
  local reason="$1"
  write_blocked_result "$reason"
  if [[ "$REQUIRE_LIVE" == "1" ]]; then
    exit 1
  fi
  exit 0
}

AWS_CLI_FOUND="no"
if command_found aws; then
  AWS_CLI_FOUND="yes"
fi
CARGO_FOUND="no"
if command_found cargo; then
  CARGO_FOUND="yes"
fi
CRATE_READY="no"
if [[ -f "$CRATE_DIR/Cargo.toml" ]]; then
  CRATE_READY="yes"
fi
SERVER_BINARY_SOURCE_READY="no"
if [[ -f "$CRATE_DIR/src/bin/nlb_live_server.rs" ]]; then
  SERVER_BINARY_SOURCE_READY="yes"
fi
CLIENT_BINARY_SOURCE_READY="no"
if [[ -f "$CRATE_DIR/src/bin/nlb_live_client.rs" ]]; then
  CLIENT_BINARY_SOURCE_READY="yes"
fi

cat >"$RESULT_DIR/manifest.env" <<EOF
run_id=$RUN_ID
started_at=$RUN_STAMP
aws_profile=${AWS_PROFILE:-default}
aws_region=$AWS_REGION
port=$PORT
nlb_protocol=$NLB_PROTOCOL
payload_bytes=$PAYLOAD_BYTES
server_timeout_secs=$SERVER_TIMEOUT_SECS
client_timeout_secs=$CLIENT_TIMEOUT_SECS
client_start_delay_seconds=$CLIENT_START_DELAY_SECONDS
target_a_server_id=$TARGET_A_SERVER_ID
target_b_server_id=$TARGET_B_SERVER_ID
require_live=$REQUIRE_LIVE
EOF

log "AWS NLB + s2n-quic live data-plane run start: $RUN_ID"

set +e
python3 "$PROJECT_ROOT/tools/check_aws_identity_readiness.py" \
  --region "$AWS_REGION" \
  --include-redacted-diagnostics \
  --output "$RESULT_DIR/aws-identity-readiness.md" \
  --json-output "$RESULT_DIR/aws-identity-readiness.json" \
  >"$LOG_DIR/aws-identity-readiness.stdout" \
  2>"$LOG_DIR/aws-identity-readiness.stderr"
AWS_READINESS_EXIT=$?
set -e

AWS_IDENTITY_OK="$(json_value "$RESULT_DIR/aws-identity-readiness.json" "identity_ok")"
AWS_IDENTITY_CLASSIFICATION="$(json_value "$RESULT_DIR/aws-identity-readiness.json" "classification")"
if [[ -z "$AWS_IDENTITY_OK" ]]; then
  AWS_IDENTITY_OK="no"
fi
if [[ -z "$AWS_IDENTITY_CLASSIFICATION" ]]; then
  AWS_IDENTITY_CLASSIFICATION="unknown"
fi

if [[ "$CRATE_READY" != "yes" ]]; then
  run_or_block "missing_s2n_nlb_cid_provider_crate"
fi
if [[ "$SERVER_BINARY_SOURCE_READY" != "yes" ]]; then
  run_or_block "missing_nlb_live_server_source"
fi
if [[ "$CLIENT_BINARY_SOURCE_READY" != "yes" ]]; then
  run_or_block "missing_nlb_live_client_source"
fi
if [[ "$CARGO_FOUND" != "yes" ]]; then
  run_or_block "missing_cargo"
fi
if [[ "$AWS_IDENTITY_OK" != "yes" ]]; then
  run_or_block "aws_identity_${AWS_IDENTITY_CLASSIFICATION}"
fi
if [[ "$AWS_READINESS_EXIT" != "0" ]]; then
  run_or_block "aws_identity_readiness_exit_${AWS_READINESS_EXIT}"
fi

require_command aws
require_command curl
require_command ssh
require_command scp
require_command tar
require_command cargo

KEY_NAME="${RESOURCE_PREFIX}-${RUN_ID}-key"
KEY_PATH="$RUN_DIR/$KEY_NAME"
SG_NAME="${RESOURCE_PREFIX}-${RUN_ID}-sg"
LB_NAME="qcm-s2n-$SHORT_STAMP"
TG_NAME="qcm-s2n-$SHORT_STAMP"
TARGET_A_NAME="${RESOURCE_PREFIX}-${RUN_ID}-s2n-a"
TARGET_B_NAME="${RESOURCE_PREFIX}-${RUN_ID}-s2n-b"
REMOTE_DIR="/home/ec2-user/s2n-quic-nlb-cid-provider"
REMOTE_PACKAGE="/home/ec2-user/s2n-quic-nlb-cid-provider.tar.gz"
REMOTE_HEALTH="/home/ec2-user/tcp-health-s2n.py"
PACKAGE_PATH="$RUN_DIR/s2n-quic-nlb-cid-provider.tar.gz"
CERT_PEM_PATH="$RUN_DIR/localhost-cert.pem"
KEY_PEM_PATH="$RUN_DIR/localhost-key.pem"

LB_ARN=""
LISTENER_ARN=""
TG_ARN=""
SG_ID=""
INSTANCE_A=""
INSTANCE_B=""
PUBLIC_IP_A=""
PUBLIC_IP_B=""
TARGETS_COLLECTED=0

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

collect_target() {
  local ip="$1"
  local target_name="$2"
  local out="$RUN_DIR/$target_name"
  mkdir -p "$out"

  ssh_quiet "$ip" "pkill -f nlb_live_server >/dev/null 2>&1 || true; pkill -f tcp-health-s2n.py >/dev/null 2>&1 || true" >/dev/null 2>&1 || true
  ssh_quiet "$ip" "cd /home/ec2-user && tar -czf ${target_name}.tgz s2n-quic-nlb-cid-provider/results s2n-quic-nlb-cid-provider/logs s2n-quic-nlb-cid-provider/server.pid tcp-health-s2n.log tcp-health-s2n.pid 2>/dev/null || true" >/dev/null 2>&1 || true
  scp_quiet "ec2-user@$ip:/home/ec2-user/${target_name}.tgz" "$out/${target_name}.tgz" >/dev/null 2>&1 || true
  if [[ -f "$out/${target_name}.tgz" ]]; then
    tar -xzf "$out/${target_name}.tgz" -C "$out" || true
  fi
}

collect_all_targets() {
  if [[ "$TARGETS_COLLECTED" == "1" ]]; then
    return 0
  fi
  if [[ -n "$PUBLIC_IP_A" ]]; then
    collect_target "$PUBLIC_IP_A" "target-a"
  fi
  if [[ -n "$PUBLIC_IP_B" ]]; then
    collect_target "$PUBLIC_IP_B" "target-b"
  fi
  TARGETS_COLLECTED=1
}

cleanup() {
  local exit_code=$?
  if [[ "${KEEP_AWS_RESOURCES:-0}" == "1" ]]; then
    manifest_set "cleanup_status" "skipped-keep-aws-resources"
    log "cleanup skipped because KEEP_AWS_RESOURCES=1"
    exit "$exit_code"
  fi

  set +e
  log "cleanup start"
  collect_all_targets >/dev/null 2>&1 || true

  if [[ -n "$LISTENER_ARN" ]]; then
    aws elbv2 delete-listener --listener-arn "$LISTENER_ARN" >/dev/null 2>&1 || true
  fi
  if [[ -n "$LB_ARN" ]]; then
    aws elbv2 delete-load-balancer --load-balancer-arn "$LB_ARN" >/dev/null 2>&1 || true
    aws elbv2 wait load-balancers-deleted --load-balancer-arns "$LB_ARN" >/dev/null 2>&1 || true
  fi
  if [[ -n "$TG_ARN" ]]; then
    if [[ -n "$INSTANCE_A" || -n "$INSTANCE_B" ]]; then
      local deregister_targets=()
      if [[ -n "$INSTANCE_A" ]]; then
        deregister_targets+=(Id="$INSTANCE_A",Port="$PORT")
      fi
      if [[ -n "$INSTANCE_B" ]]; then
        deregister_targets+=(Id="$INSTANCE_B",Port="$PORT")
      fi
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

  manifest_set "cleanup_status" "deleted-listener-lb-tg-instances-sg-keypair"
  log "cleanup done"
  exit "$exit_code"
}
trap cleanup EXIT

start_target() {
  local ip="$1"
  local target_name="$2"
  local server_id="$3"

  log "bootstrap target $target_name at $ip"
  scp_quiet "$PACKAGE_PATH" "ec2-user@$ip:$REMOTE_PACKAGE"
  ssh_quiet "$ip" "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR && tar -xzf $REMOTE_PACKAGE -C $REMOTE_DIR"
  scp_quiet "$CERT_PEM_PATH" "ec2-user@$ip:$REMOTE_DIR/localhost-cert.pem"
  scp_quiet "$KEY_PEM_PATH" "ec2-user@$ip:$REMOTE_DIR/localhost-key.pem"

  ssh_quiet "$ip" "bash -lc 'set -euo pipefail
sudo dnf install -y curl gcc gcc-c++ cmake perl tar gzip openssl-devel pkgconf-pkg-config python3 git >/tmp/s2n-bootstrap-dnf.log 2>&1
if [[ ! -x \"\$HOME/.cargo/bin/cargo\" ]]; then
  curl --proto =https --tlsv1.2 -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal >/tmp/s2n-rustup.log 2>&1
fi
source \"\$HOME/.cargo/env\"
rustup default stable >/tmp/s2n-rustup-default.log 2>&1
rustc --version
cargo --version
'" | tee "$LOG_DIR/bootstrap-$target_name.log"

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
nohup python3 -u $REMOTE_HEALTH > /home/ec2-user/tcp-health-s2n.log 2>&1 & echo \$! > /home/ec2-user/tcp-health-s2n.pid"

  ssh_quiet "$ip" "bash -lc 'set -euo pipefail
source \"\$HOME/.cargo/env\"
cd $REMOTE_DIR
cargo build --release --bins
mkdir -p results logs
SERVER_ID=$server_id LISTEN_ADDR=0.0.0.0:$PORT CERT_PEM_PATH=localhost-cert.pem KEY_PEM_PATH=localhost-key.pem RESULT_PATH=results/server.json TIMEOUT_SECS=$SERVER_TIMEOUT_SECS nohup target/release/nlb_live_server > logs/nlb-live-server.stdout 2> logs/nlb-live-server.stderr & echo \$! > server.pid
sleep 5
if ! kill -0 \$(cat server.pid) >/dev/null 2>&1; then
  echo \"s2n live server process is not running\" >&2
  tail -120 logs/nlb-live-server.stderr >&2 || true
  exit 1
fi
echo s2n-live-server-started
'" | tee "$LOG_DIR/server-start-$target_name.log"
}

log "package s2n-quic NLB CID provider crate"
tar -czf "$PACKAGE_PATH" \
  --exclude './target' \
  --exclude './results' \
  -C "$CRATE_DIR" .
manifest_set "package_path" "$PACKAGE_PATH"

log "generate short-lived localhost certificate with rcgen"
cargo run --manifest-path "$CRATE_DIR/Cargo.toml" --quiet --bin generate_localhost_cert \
  "$CERT_PEM_PATH" \
  "$KEY_PEM_PATH" \
  >"$LOG_DIR/generate-localhost-cert.stdout" \
  2>"$LOG_DIR/generate-localhost-cert.stderr"

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

log "create SSH key pair"
ssh-keygen -t ed25519 -N "" -C "$KEY_NAME" -f "$KEY_PATH" >/dev/null
chmod 600 "$KEY_PATH"
aws ec2 import-key-pair --key-name "$KEY_NAME" --public-key-material "fileb://${KEY_PATH}.pub" >"$LOG_DIR/import-key-pair.json"
manifest_set "key_name" "$KEY_NAME"

log "create target security group"
SG_ID="$(aws ec2 create-security-group --group-name "$SG_NAME" --description "s2n QUIC NLB live $RUN_ID" --vpc-id "$VPC_ID" --query GroupId --output text)"
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
manifest_set "public_ip_a" "$PUBLIC_IP_A"
manifest_set "public_ip_b" "$PUBLIC_IP_B"
aws ec2 describe-instances --instance-ids "$INSTANCE_A" "$INSTANCE_B" >"$LOG_DIR/instances.json"

log "wait SSH"
wait_for_ssh "$PUBLIC_IP_A"
wait_for_ssh "$PUBLIC_IP_B"

start_target "$PUBLIC_IP_A" "target-a" "$TARGET_A_SERVER_ID"
start_target "$PUBLIC_IP_B" "target-b" "$TARGET_B_SERVER_ID"

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

log "run s2n client through NLB $LB_DNS:$PORT"
if (( CLIENT_START_DELAY_SECONDS > 0 )); then
  sleep "$CLIENT_START_DELAY_SECONDS"
fi
CLIENT_RESULT="$RUN_DIR/client/results/client.json"
CLIENT_EXIT=0
SERVER_ADDR="$LB_DNS:$PORT" \
  SERVER_NAME=localhost \
  CERT_PEM_PATH="$CERT_PEM_PATH" \
  PAYLOAD_BYTES="$PAYLOAD_BYTES" \
  TIMEOUT_SECS="$CLIENT_TIMEOUT_SECS" \
  RESULT_PATH="$CLIENT_RESULT" \
  cargo run --manifest-path "$CRATE_DIR/Cargo.toml" --release --bin nlb_live_client \
  >"$LOG_DIR/client.stdout" \
  2>"$LOG_DIR/client.stderr" || CLIENT_EXIT=$?
manifest_set "client_exit_code" "$CLIENT_EXIT"

sleep 8
collect_all_targets

log "write summary"
python3 - "$RUN_DIR" <<'PY'
import json
import pathlib
import sys

run = pathlib.Path(sys.argv[1])
client_path = run / "client" / "results" / "client.json"
client = json.loads(client_path.read_text()) if client_path.exists() else {}
servers = []
for target in ("target-a", "target-b"):
    for path in (run / target).glob("**/results/server.json"):
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            data = {"status": "ERROR", "error": str(exc)}
        data["_target"] = target
        data["_path"] = str(path)
        servers.append(data)

successful_servers = [s for s in servers if s.get("status") == "PASS"]
positive_pass = client.get("status") == "PASS" and client.get("echo_matches") is True and len(successful_servers) == 1
summary = {
    "status": "PASS" if positive_pass else "FAIL_CLASSIFIED",
    "claim_boundary": "s2n NLB forwarding echo only; not active connection migration",
    "client_status": client.get("status"),
    "client_echo_matches": client.get("echo_matches"),
    "client_payload_bytes": client.get("payload_bytes"),
    "client_received_bytes": client.get("received_bytes"),
    "server_success_count": len(successful_servers),
    "successful_target": successful_servers[0].get("_target") if successful_servers else None,
    "servers": servers,
}
(run / "results" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(run / "results" / "result.env").write_text(
    "\n".join([
        f"run_id={run.name}",
        f"validation={'ok' if positive_pass else 'failed'}",
        f"client_status={client.get('status')}",
        f"client_echo_matches={client.get('echo_matches')}",
        f"server_success_count={len(successful_servers)}",
        f"successful_target={successful_servers[0].get('_target') if successful_servers else ''}",
        "claim_boundary=s2n_nlb_forwarding_echo_not_active_migration",
        "",
    ])
)
print(json.dumps(summary, indent=2))
PY

log "AWS NLB + s2n-quic live data-plane run complete"
exit "$CLIENT_EXIT"
