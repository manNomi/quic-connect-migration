# AWS NLB HTTP/3 Mid-flight Workload Results

작성일: 2026-06-24  
상태: PASS  
목적: HTTP/3 request/response body가 전송 중인 상태에서 active QUIC Connection Migration을 수행해도 작업이 완료되는지 검증한다.

## 1. Question

이전 HTTP/3 workload gate는 request 사이의 migration만 검증했다.

```text
POST /upload before
  -> AddPath -> Probe -> Switch
  -> GET /download after
```

이번 실험은 더 강한 조건을 검증한다.

```text
HTTP/3 body transfer starts
  -> migration threshold reached
  -> AddPath -> Probe -> Switch
  -> same HTTP/3 body transfer completes
```

## 2. Harness Changes

수정/추가한 파일:

- `experiments/quic-go-min-repro/cmd/h3client/main.go`
- `experiments/quic-go-min-repro/cmd/h3server/main.go`
- `experiments/quic-go-min-repro/scripts/run-h3-client.sh`
- `experiments/quic-go-min-repro/scripts/run-local-h3-midflight.sh`
- `harness/scripts/run-aws-nlb-quic-data-plane.sh`

추가한 client modes:

| mode | 의미 |
| --- | --- |
| `midflight-upload` | POST `/upload` body reader가 threshold 도달 시 migration trigger |
| `midflight-download` | GET `/download?stream=true` response reader가 threshold 도달 시 migration trigger |

서버는 `stream=true` download에서 response body를 chunk 단위로 천천히 전송한다.

## 3. Local Gate

Command:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

Artifact:

- `experiments/quic-go-min-repro/artifacts/local-h3-midflight-check/`

결과:

| workload | status | socket A | socket B | final addr | migration threshold | task evidence |
| --- | --- | --- | --- | --- | ---: | --- |
| mid-flight upload | PASS | `[::]:53663` | `[::]:63569` | `[::]:63569` | 532480 bytes | server decoded 1MiB upload |
| mid-flight download | PASS | `[::]:49959` | `[::]:52767` | `[::]:52767` | 524288 bytes | client decoded 1MiB download |

qlog 요약:

| workload | ALPN h3 | HTTP/3 frame evidence | PATH_CHALLENGE/PATH_RESPONSE lines |
| --- | ---: | ---: | ---: |
| mid-flight upload | observed | observed | 12 |
| mid-flight download | observed | observed | 12 |

관찰:

`path.Switch()` 직후의 `conn.LocalAddr()`는 socket A로 남아 있었지만, workload 완료 후 최종 주소는 socket B였다. 따라서 mid-flight case에서는 `Switch()` 즉시 반환값보다 후속 packet 송수신 이후의 final connection address와 qlog path validation을 함께 봐야 한다.

## 4. AWS NLB TCP_QUIC `:443` Gate

공통 조건:

| 항목 | 값 |
| --- | --- |
| NLB protocol | `TCP_QUIC` |
| port | `443` |
| target count | 2 |
| CID format | `0x00 + 8-byte Server ID + 7-byte nonce` |
| payload | 1MiB |
| migration | client socket A -> socket B, `AddPath -> Probe -> Switch` |

### 4.1 Mid-flight Upload

Command:

```bash
RUN_ID=aws-nlb-h3-midflight-upload-20260623T172119Z \
WORKLOAD=h3-midflight-upload \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
TIMEOUT=120s \
SERVER_TIMEOUT=600s \
POST_SEND_WAIT=3s \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

Artifact:

- `harness/results/aws-nlb-h3-midflight-upload-20260623T172119Z/`

결과:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| successful target | target-a |
| client socket A | `[::]:56276` |
| client socket B | `[::]:52824` |
| final client addr | `[::]:52824` |
| migration threshold | 532480 bytes |
| server remote addr | `211.60.158.133:56276` |
| server workload | upload |
| server decoded bytes | 1048576 |
| qlog path evidence | 3 PATH_CHALLENGE/PATH_RESPONSE lines |
| cleanup | listener, NLB, target group, EC2, SG, key pair deleted |

### 4.2 Mid-flight Download

첫 download 실행은 client dial 단계에서 `timeout: no recent network activity`로 실패했다. 이 실패는 socket B 생성 전 발생했으므로 mid-flight migration failure가 아니라 NLB readiness timing 또는 transient handshake failure로 분류했다.

재시도에서는 target health 2/2 이후 `CLIENT_START_DELAY_SECONDS=8`을 두고 성공했다.

Command:

```bash
RUN_ID=aws-nlb-h3-midflight-download-retry-20260623T173500Z \
WORKLOAD=h3-midflight-download \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
TIMEOUT=120s \
SERVER_TIMEOUT=600s \
POST_SEND_WAIT=3s \
CLIENT_START_DELAY_SECONDS=8 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

Artifact:

- `harness/results/aws-nlb-h3-midflight-download-retry-20260623T173500Z/`

결과:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| successful target | target-b |
| client socket A | `[::]:61456` |
| client socket B | `[::]:63381` |
| final client addr | `[::]:63381` |
| migration threshold | 524288 bytes |
| server remote addr | `211.60.158.133:61456` |
| server workload | streaming download |
| response bytes | 1048576 |
| stream chunk | 16384 bytes, 2ms delay |
| qlog path evidence | 3 PATH_CHALLENGE/PATH_RESPONSE lines |
| cleanup | listener, NLB, target group, EC2, SG, key pair deleted |

## 5. Residue Check

RunId 기준으로 활성 리소스가 남아있지 않음을 확인했다.

| resource | result |
| --- | --- |
| EC2 pending/running/stopping/stopped | none |
| security group | none |
| NLB | none |
| target group | none |
| key pair | none |

## 6. Interpretation

이번 챕터로 증거 체인은 다음까지 확장됐다.

```text
custom QUIC stream continuity
  -> AWS NLB CID-aware transport continuity
  -> HTTP/3 post-migration request continuity
  -> HTTP/3 mid-flight body transfer continuity
```

논문에서 말할 수 있는 주장:

> Under a controlled quic-go client and an AWS NLB `TCP_QUIC :443` passthrough deployment with correctly encoded QUIC-LB plaintext CIDs, both a 1MiB HTTP/3 upload and a 1MiB streaming download can complete when active client-side migration is triggered while the body is in flight.

주의할 점:

1. 이 결과는 browser/Chrome/Cronet policy를 검증한 것이 아니다.
2. 실제 Wi-Fi/LTE interface handover가 아니라 controlled source-port path change다.
3. NLB success는 backend CID format과 registered `QuicServerId`가 맞을 때만 성립한다.
4. 첫 download attempt의 dial timeout은 NLB readiness timing을 실험 통제 변수로 남긴다.
