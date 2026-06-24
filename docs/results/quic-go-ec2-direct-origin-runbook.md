# quic-go EC2 Direct-Origin Runbook

작성일: 2026-06-22  
상태: 실행 패키지 준비 완료, 실제 EC2 프로비저닝은 AWS credential 문제로 보류  
대상 코드: `experiments/quic-go-min-repro/`

## 1. Purpose

local loopback에서 성공한 quic-go Connection Migration 최소 재현을 EC2 public IPv4 direct-origin 환경으로 확장한다.

검증 질문:

> CDN/LB 없이 public network path에서 custom QUIC client가 UDP socket A에서 연결한 뒤 socket B로 active migration을 수행할 때, `AddPath -> Probe -> Switch`와 application payload continuity가 유지되는가?

## 2. Current AWS CLI State

로컬 AWS CLI 상태:

```text
aws cli: installed
configured region: ap-northeast-2
aws sts get-caller-identity: InvalidClientTokenId
```

해석:

- AWS CLI는 설치되어 있다.
- credential이 만료되었거나 잘못되어 현재 EC2 생성/조회는 불가능하다.
- 실제 EC2 실행 전 `aws sts get-caller-identity`가 성공해야 한다.

확인 명령:

```bash
aws configure list
aws sts get-caller-identity
```

## 3. Prepared Scripts

위치:

```text
experiments/quic-go-min-repro/scripts/
  run-local-happy-path.sh
  run-server.sh
  run-ec2-client.sh
  package-for-ec2.sh
  ec2-bootstrap-go.sh
```

용도:

- `run-local-happy-path.sh`: local regression check
- `run-server.sh`: EC2 또는 local server 실행
- `run-ec2-client.sh`: local machine에서 EC2 public IP로 client 실행
- `package-for-ec2.sh`: EC2 업로드용 tarball 생성
- `ec2-bootstrap-go.sh`: EC2에 Go toolchain과 tcpdump 설치

## 4. EC2 Requirements

권장 최소 구성:

```text
AMI: Amazon Linux 2023
Instance type: t3.micro or t4g.micro
Region: ap-northeast-2
Public IPv4: enabled
Storage: 8 GB+
```

Security group inbound:

```text
TCP 22    from <your-client-public-ip>/32
UDP 4242  from <your-client-public-ip>/32
```

Security group outbound:

```text
All outbound or at least ephemeral UDP/TCP outbound
```

주의:

- UDP 4242를 열지 않으면 QUIC handshake가 실패한다.
- `0.0.0.0/0`로 열 수는 있지만 실험용이면 client public IP `/32`가 낫다.
- 이 단계는 AWS 비용이 발생할 수 있으므로 실험 후 instance를 stop/terminate해야 한다.

## 5. Package Locally

로컬에서:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
./scripts/package-for-ec2.sh
```

예시 출력:

```text
/Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro/artifacts/packages/quic-go-min-repro-20260622T084559Z.tar.gz
```

## 6. Upload to EC2

변수:

```bash
EC2_HOST=<ec2-public-ip>
SSH_KEY=</path/to/key.pem>
PACKAGE=artifacts/packages/quic-go-min-repro-20260622T084559Z.tar.gz
```

업로드:

```bash
scp -i "$SSH_KEY" "$PACKAGE" "ec2-user@${EC2_HOST}:~/"
```

EC2 접속:

```bash
ssh -i "$SSH_KEY" "ec2-user@${EC2_HOST}"
```

## 7. Bootstrap EC2

EC2에서:

```bash
mkdir -p ~/quic-go-min-repro
tar -xzf ~/quic-go-min-repro-*.tar.gz -C ~/quic-go-min-repro
cd ~/quic-go-min-repro
./scripts/ec2-bootstrap-go.sh
source ~/.profile
go version
```

## 8. Run Server on EC2

EC2 terminal 1:

```bash
cd ~/quic-go-min-repro
LISTEN_ADDR=0.0.0.0:4242 \
TIMEOUT=120s \
ARTIFACT_DIR=artifacts/ec2-server-$(date -u +%Y%m%dT%H%M%SZ) \
./scripts/run-server.sh
```

Optional EC2 tcpdump in another EC2 terminal:

```bash
sudo mkdir -p /tmp/quic-cm-pcap
sudo tcpdump -i any -w /tmp/quic-cm-pcap/quic-go-ec2-server.pcap 'udp port 4242'
```

## 9. Run Client Locally

로컬에서:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
SERVER_ADDR=<ec2-public-ip>:4242 \
BIND_ADDR=0.0.0.0:0 \
PROBE_TIMEOUT=5s \
TIMEOUT=60s \
./scripts/run-ec2-client.sh
```

성공하면 local client artifact가 다음 형태로 생성된다.

```text
artifacts/ec2-client-<timestamp>/
  logs/client.jsonl
  logs/client.stdout.log
  results/client.json
  results/qlog-path-validation.txt
  qlog/*.sqlog
  keylog/client.keys
```

## 10. Collect Server Artifacts

서버 artifact path는 `run-server.sh` 실행 시 출력/환경변수로 정한 `ARTIFACT_DIR`이다.

예시:

```bash
EC2_HOST=<ec2-public-ip>
SSH_KEY=</path/to/key.pem>
REMOTE_ARTIFACT=~/quic-go-min-repro/artifacts/ec2-server-20260622T090000Z
LOCAL_DEST=artifacts/ec2-server-collected-20260622T090000Z

mkdir -p "$LOCAL_DEST"
scp -i "$SSH_KEY" -r "ec2-user@${EC2_HOST}:${REMOTE_ARTIFACT}/"* "$LOCAL_DEST/"
scp -i "$SSH_KEY" "ec2-user@${EC2_HOST}:/tmp/quic-cm-pcap/quic-go-ec2-server.pcap" "$LOCAL_DEST/" || true
```

## 11. Validation Checklist

Client:

```bash
cat artifacts/ec2-client-*/results/client.json
rg -n "path_challenge|path_response" artifacts/ec2-client-*/qlog
```

Server:

```bash
cat artifacts/ec2-server-collected-*/results/server.json
rg -n "path_challenge|path_response" artifacts/ec2-server-collected-*/qlog
```

Success criteria:

- client `ok: true`
- server `ok: true`
- `switch_before_probe_matched: true`
- client qlog has `path_challenge` and `path_response`
- server qlog has `path_challenge` and `path_response`
- server receives both `before` and `after` payloads on one accepted QUIC connection
- payload SHA-256 values match between client and server
- tcpdump shows QUIC packets on UDP 4242

Tuple-change interpretation:

- If the local client stays on the same physical network, source IP may not change.
- Creating socket B should still produce a different source port, either locally or through NAT.
- Server `conn.RemoteAddr()` is a connection-level current path observation, not a packet-level per-stream tuple.
- For precise before/after tuple evidence, use tcpdump or packet-level qlog/pcap analysis.

## 12. Expected Result Row

실험 후 `Minimal Data Schema`에 넣을 값:

```text
trial_id: quic-go-ec2-direct-origin-001
client_type: quic-go custom client
server_implementation: quic-go
deployment_tier: EC2 direct origin
protocol: QUIC transport stream
migration_trigger: client socket A -> socket B, AddPath -> Probe -> Switch
path_validation_observed: true if qlog path_challenge/path_response exists
application_task: before/after 1 MiB unidirectional stream payload
application_success: true if both payloads received with matching SHA-256
manual_intervention_required: false during transfer
failure_layer: none on success
```

## 13. Failure Diagnosis

Handshake timeout:

- Security group UDP 4242 missing
- EC2 server not listening on `0.0.0.0:4242`
- local network blocks outbound UDP

`path.Probe()` timeout:

- return packets from EC2 blocked
- NAT/firewall drops second UDP socket traffic
- server crashed after first stream

server receives only `before`:

- migration path validation failed after first payload
- client artifact `client.stdout.log` should contain the exact error
- check qlog for missing `path_response`

qlog missing:

- `--qlog-dir` path not writable
- script not used or environment cleared

## 14. Cleanup

After the trial:

```bash
# Stop tcpdump if running.
sudo pkill tcpdump || true
```

AWS cleanup:

- stop or terminate the EC2 instance
- remove temporary security group rules if they were created only for this experiment
- archive local and server artifacts under the research folder

## 15. Current Blocker

Actual EC2 provisioning was not performed in this run because AWS credentials are currently invalid.

Next unblock action:

```bash
aws sts get-caller-identity
```

Once that succeeds, create or reuse an EC2 instance and follow this runbook from section 5.
