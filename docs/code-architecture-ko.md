# 코드와 하네스 구조 설명

작성일: 2026-06-24  
목적: 실험에 사용한 코드가 어떤 방식으로 Connection Migration을 만들고 관찰했는지 정리한다.

## 1. 전체 코드 구조

```text
repro/quic-go-min-repro/
├── cmd/
│   ├── client/
│   │   └── main.go          # QUIC transport stream client
│   ├── server/
│   │   └── main.go          # QUIC transport stream server
│   ├── h3client/
│   │   └── main.go          # HTTP/3 workload client
│   └── h3server/
│       └── main.go          # HTTP/3 workload server
├── internal/common/
│   ├── aws_nlb_cid.go       # AWS NLB QUIC-LB plaintext CID generator
│   ├── logging.go           # JSONL/result JSON helper
│   ├── payload.go           # deterministic payload and checksum
│   └── tls.go               # self-signed TLS config
└── scripts/
    ├── run-local-happy-path.sh
    ├── run-local-h3-workload.sh
    ├── run-local-h3-midflight.sh
    ├── run-chrome-h3-local.sh
    ├── run-server.sh
    ├── run-h3-server.sh
    ├── run-ec2-client.sh
    └── run-h3-client.sh
```

AWS 하네스:

```text
harness/
├── config/
│   ├── aws.env.example
│   └── experiment.env.example
├── manifests/
│   └── experiment-matrix.csv
└── scripts/
    ├── _lib.sh
    ├── aws-preflight.sh
    ├── package-quic-go-ec2.sh
    ├── run-aws-nlb-quic-data-plane.sh
    ├── run-local-quic-go.sh
    └── validate-quic-go-artifacts.sh
```

## 2. QUIC transport stream client/server

### 2.1 목적

HTTP/3 없이 QUIC transport connection 자체가 migration 이후에도 stream payload를 유지하는지 확인한다.

### 2.2 Server

파일:

- `repro/quic-go-min-repro/cmd/server/main.go`

역할:

1. UDP address에 QUIC server listen.
2. self-signed TLS config 사용.
3. client stream을 accept.
4. deterministic payload message를 수신하고 checksum 검증.
5. before/after stream을 같은 connection에서 받았는지 result JSON에 기록.
6. AWS NLB 실험에서는 custom Connection ID generator를 사용해 Server ID를 CID에 encode.

### 2.3 Client

파일:

- `repro/quic-go-min-repro/cmd/client/main.go`

핵심 동작:

```text
socket A 생성
  -> QUIC Dial
  -> before stream 전송
  -> socket B 생성
  -> conn.AddPath(transport B)
  -> path.Switch() before Probe, ErrPathNotValidated 확인
  -> path.Probe()
  -> path.Switch()
  -> after stream 전송
  -> final local addr 확인
```

중요한 검증:

- probe 전 `Switch()`는 실패해야 한다.
- 실패 error가 `quic.ErrPathNotValidated`와 match되어야 한다.
- `Probe()` 이후 `Switch()`가 성공해야 한다.
- migration 후 payload checksum이 맞아야 한다.

## 3. HTTP/3 workload server/client

## 3.1 h3server

파일:

- `repro/quic-go-min-repro/cmd/h3server/main.go`

endpoint:

| Method | Path | 역할 |
| --- | --- | --- |
| POST | `/upload` | request body를 읽고 deterministic message checksum 검증 |
| GET | `/download` | deterministic response body 생성 |
| GET | `/browser-sequence` | Chrome page+subresource baseline용 HTML 생성 |
| GET | `/pixel` | Chrome subresource baseline용 SVG image 생성 |
| GET | `/browser-poll` | Chrome long-lived polling baseline용 HTML/JS 생성 |
| GET | `/poll` | Chrome polling fetch request에 JSON response 반환 |

특수 query:

| query | 의미 |
| --- | --- |
| `bytes` | response payload size |
| `label` | payload label |
| `stream=true` | response를 chunk 단위로 천천히 write |
| `chunk_bytes` | streaming response chunk size |
| `delay_ms` | chunk 간 delay |

server result에 기록하는 값:

- method/path
- remote addr
- request bytes
- response bytes
- request SHA256
- response SHA256
- workload type
- stream response 여부
- decode success 여부

## 3.2 h3client

파일:

- `repro/quic-go-min-repro/cmd/h3client/main.go`

지원 mode:

| mode | 설명 |
| --- | --- |
| `upload-download` | POST `/upload` 완료 후 migration, GET `/download` 실행 |
| `midflight-upload` | POST body 전송 중 threshold에서 migration |
| `midflight-download` | streaming GET response 수신 중 threshold에서 migration |

공통 migration 흐름:

```text
UDP socket A
  -> QUIC Dial
  -> HTTP/3 ClientConn 생성
  -> UDP socket B
  -> conn.AddPath()
  -> path.Switch() before Probe로 guardrail 확인
  -> path.Probe()
  -> path.Switch()
```

## 4. HTTP/3 post-migration request 실험

script:

- `repro/quic-go-min-repro/scripts/run-local-h3-workload.sh`

흐름:

```text
h3server start
  -> h3client mode=upload-download
  -> POST /upload before
  -> migration
  -> GET /download after
  -> result JSON validation
```

검증:

- client `ok=true`
- server `ok=true`
- client task count 2
- server request count 2
- final local addr가 socket B
- qlog에서 ALPN h3, HTTP/3 frame, PATH_CHALLENGE/PATH_RESPONSE 확인

## 5. HTTP/3 mid-flight 실험

script:

- `repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh`

### 5.1 Mid-flight upload

핵심 아이디어:

request body reader가 데이터를 chunk 단위로 읽히다가 threshold 이상 전송되면 migration을 trigger한다.

```text
POST /upload starts
  -> body reader sends chunks
  -> bytes >= migration threshold
  -> AddPath -> Probe -> Switch
  -> remaining body continues
  -> server validates full body checksum
```

주요 파라미터:

| 변수 | 기본값 |
| --- | --- |
| `PAYLOAD_BYTES` | 1048576 |
| `MIGRATION_AT_BYTES` | 0, 즉 대략 절반 |
| `CHUNK_BYTES` | 16384 |
| `CHUNK_DELAY` | 2ms |

### 5.2 Mid-flight download

핵심 아이디어:

server가 response body를 streaming chunk로 보내고, client response reader가 threshold 이상 수신하면 migration을 trigger한다.

```text
GET /download?stream=true starts
  -> server writes response chunks
  -> client reads chunks
  -> bytes >= migration threshold
  -> AddPath -> Probe -> Switch
  -> remaining response continues
  -> client validates full body checksum
```

### 5.3 mid-flight 실험에서 주의할 점

`path.Switch()` 직후 `conn.LocalAddr()`가 즉시 socket B로 보이지 않을 수 있다.

관찰된 현상:

```text
path.Switch() 직후 local addr: socket A
workload 완료 후 final addr: socket B
```

따라서 성공 기준은 다음을 함께 봐야 한다.

1. final addr가 socket B인지
2. qlog에 path validation evidence가 있는지
3. payload checksum이 맞는지
4. manual retry 없이 HTTP/3 task가 완료됐는지

## 6. AWS NLB CID generator

파일:

- `repro/quic-go-min-repro/internal/common/aws_nlb_cid.go`

목적:

AWS NLB가 target routing에 사용할 수 있도록 backend-generated CID에 Server ID를 encode한다.

형식:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

왜 필요한가:

- QUIC migration 후 client source IP/port가 바뀌면 5-tuple 기반 routing은 같은 target을 보장하지 못한다.
- AWS NLB는 QUIC CID 내부의 Server ID를 사용해 target을 선택할 수 있다.
- 따라서 backend QUIC server가 NLB가 기대하는 CID format을 생성해야 한다.

negative control에서 확인한 것:

- `8-byte Server ID + 8-byte nonce`처럼 첫 byte `0x00`이 빠진 malformed layout은 실패했다.
- target 등록 `QuicServerId`와 CID 안의 Server ID가 다르면 target health가 정상이어도 handshake/application payload가 실패했다.

## 7. AWS 하네스

파일:

- `harness/scripts/run-aws-nlb-quic-data-plane.sh`

역할:

1. AWS preflight 실행.
2. quic-go repro package 생성.
3. SSH key pair 생성.
4. Security group 생성.
5. EC2 target A/B 생성.
6. target에 Go runtime과 repro code 배포.
7. TCP health sidecar 실행.
8. target별 QUIC/H3 server 실행.
9. NLB와 target group 생성.
10. target을 `QuicServerId`와 함께 등록.
11. target health 2/2 대기.
12. local client를 NLB DNS로 실행.
13. target artifacts 수집.
14. summary JSON 작성.
15. listener, NLB, target group, EC2, SG, key pair cleanup.

지원 workload:

| `WORKLOAD` | client/server |
| --- | --- |
| `transport` | `cmd/client`, `cmd/server` |
| `h3` | `cmd/h3client --mode upload-download`, `cmd/h3server` |
| `h3-midflight-upload` | `cmd/h3client --mode midflight-upload`, `cmd/h3server` |
| `h3-midflight-download` | `cmd/h3client --mode midflight-download`, `cmd/h3server` |

지원 protocol:

| 변수 | 예 |
| --- | --- |
| `NLB_PROTOCOL` | `QUIC`, `TCP_QUIC` |
| `PORT` | `4242`, `443` |

## 8. Chrome 브라우저 baseline

script:

- `repro/quic-go-min-repro/scripts/run-chrome-h3-local.sh`

목적:

Chrome browser가 quic-go H3 test origin으로 실제 HTTP/3 request를 보낼 수 있는지 확인한다. 이 실험은 migration 실험이 아니라 browser baseline이다.

지원 workload:

| `WORKLOAD` | 요청 |
| --- | --- |
| `single` | `GET /download?bytes=128&label=chrome-baseline` |
| `sequence` | `GET /browser-sequence`, two `GET /pixel` subresources |
| `poll` | `GET /browser-poll`, sequential `GET /poll` fetch requests |

흐름:

```text
openssl로 local test cert/key 생성
  -> cert SPKI hash 계산
  -> quic-go h3server를 cert/key로 실행
  -> Chrome headless 실행
  -> --origin-to-force-quic-on=127.0.0.1:4443
  -> --ignore-certificate-errors-spki-list=<SPKI>
  -> Chrome NetLog, server JSON, qlog 수집
```

성공 기준:

- Chrome NetLog에 `QUIC_SESSION`이 존재
- Chrome NetLog의 target origin `HTTP_STREAM_JOB`에 `using_quic=true`
- `single`에서는 server가 `GET /download` request를 수신
- `sequence`에서는 server가 HTML page와 subresource request를 모두 수신
- `poll`에서는 server가 page request와 sequential fetch request를 모두 수신
- qlog에 `chosen_alpn`과 `http3:frame` evidence가 있음

주의:

headless Chrome이 binary response 이후 clean exit하지 않고 timeout될 수 있다. 이 경우에도 server request, NetLog, qlog evidence가 모두 있으면 baseline은 PASS로 분류한다.

classifier:

- `tools/classify_chrome_h3_artifacts.py`

이 tool은 Chrome artifact directory를 입력받아 다음을 판정한다.

| classification | 의미 |
| --- | --- |
| `no_path_change_baseline` | tuple change와 path validation이 없는 정상 baseline |
| `possible_connection_migration` | tuple change, qlog path validation, target QUIC session 1개 |
| `reconnect_or_multiple_sessions` | tuple change와 여러 target QUIC session |
| `tuple_changed_without_path_validation` | tuple change는 있으나 path validation evidence 없음 |
| `browser_h3_request_failed` | browser workload가 H3로 완료되지 않음 |

## 9. 실행 예시

### 9.1 Local QUIC transport

```bash
cd repro/quic-go-min-repro
./scripts/run-local-happy-path.sh
```

### 9.2 Local HTTP/3 post-migration workload

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
```

### 9.3 Local HTTP/3 mid-flight workload

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

### 9.4 Chrome local HTTP/3 baseline

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=poll NETWORK_CHANGE_AFTER_SECONDS=2 NETWORK_CHANGE_CMD='...' RUN_ID=chrome-h3-poll-network-change ./scripts/run-chrome-h3-local.sh
```

### 9.5 AWS NLB transport

```bash
WORKLOAD=transport \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 9.6 AWS NLB HTTP/3 post-migration

```bash
WORKLOAD=h3 \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 9.7 AWS NLB HTTP/3 mid-flight upload

```bash
WORKLOAD=h3-midflight-upload \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 9.8 AWS NLB HTTP/3 mid-flight download

```bash
WORKLOAD=h3-midflight-download \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
CLIENT_START_DELAY_SECONDS=8 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

## 10. 검증 명령

Go test:

```bash
cd repro/quic-go-min-repro
go test ./...
```

Bash syntax:

```bash
bash -n harness/scripts/run-aws-nlb-quic-data-plane.sh
bash -n repro/quic-go-min-repro/scripts/run-chrome-h3-local.sh
bash -n repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh
bash -n repro/quic-go-min-repro/scripts/run-h3-client.sh
python3 -m py_compile tools/classify_chrome_h3_artifacts.py
```

CSV parse:

```bash
python3 - <<'PY'
import csv
for path in [
    "data/experiment-results.csv",
    "data/implementation-survey.csv",
    "harness/manifests/experiment-matrix.csv",
]:
    rows = list(csv.DictReader(open(path)))
    print(path, len(rows))
PY
```

## 11. 공개 repo에서 제외한 것

이 저장소에는 source와 문서만 포함했다.

제외 항목:

- AWS credential
- local `harness/config/aws.env`
- keylog
- qlog raw file
- pcap
- EC2 SSH key
- AWS 실행 artifact
- `.tar.gz` package

실험 결과 값은 [experiment-report-ko.md](experiment-report-ko.md), [data/experiment-results.csv](../data/experiment-results.csv), [docs/results](results/) 문서에 요약했다.
