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
    ├── run-chrome-h3-alt-svc.sh
    ├── run-chrome-public-h3.sh
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
│   ├── controlled-public-origin.env.example
│   └── experiment.env.example
├── manifests/
│   └── experiment-matrix.csv
└── scripts/
    ├── _lib.sh
    ├── aws-preflight.sh
    ├── controlled-public-preflight.sh
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
| GET | `/browser-slow` | Chrome slow subresource network-change control용 HTML 생성 |
| GET | `/slow-js` | chunk delay가 있는 streaming JavaScript subresource |

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

controlled public origin preflight:

- `harness/config/controlled-public-origin.env.example`
- `harness/scripts/controlled-public-preflight.sh`

역할:

1. local-only public origin config를 로드한다.
2. public URL, baseline summary, server artifact, secondary path, `NETWORK_CHANGE_CMD`를 통합 점검한다.
3. ignored artifact directory에 readiness JSON/Markdown을 남긴다.
4. server, baseline, network-change 실행 command template을 출력한다.

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
| `slow` | `GET /browser-slow`, streaming `GET /slow-js` subresource |

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

주소 설정:

| 변수 | 의미 |
| --- | --- |
| `ADDR` | 기본 listen/origin 주소 |
| `LISTEN_ADDR` | h3server가 bind할 주소. 기본값은 `ADDR` |
| `ORIGIN_ADDR` | Chrome이 접속하고 forced QUIC를 적용할 origin 주소. 기본값은 `ADDR` |

`LISTEN_ADDR=0.0.0.0:4443`, `ORIGIN_ADDR=<Wi-Fi IP>:4443` 조합으로 non-loopback local origin 실험을 수행할 수 있다.

성공 기준:

- Chrome NetLog에 `QUIC_SESSION`이 존재
- Chrome NetLog의 target origin `HTTP_STREAM_JOB`에 `using_quic=true`
- `single`에서는 server가 `GET /download` request를 수신
- `sequence`에서는 server가 HTML page와 subresource request를 모두 수신
- `poll`에서는 server가 page request와 sequential fetch request를 모두 수신
- `slow`에서는 server가 page request와 streaming subresource request를 모두 수신
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

## 9. Chrome natural Alt-Svc control

script:

- `repro/quic-go-min-repro/scripts/run-chrome-h3-alt-svc.sh`

목적:

강제 QUIC flag 없이, TCP HTTPS response의 `Alt-Svc: h3=":4443"; ma=60` 광고만으로 Chrome이 다음 request를 HTTP/3로 전환하는지 확인한다. 이 실험은 migration 실험이 아니라 natural browser HTTP/3 discovery control이다.

흐름:

```text
openssl로 local test cert/key 생성
  -> cert SPKI hash 계산
  -> h3server가 UDP HTTP/3 listener와 TCP HTTPS listener를 동시에 실행
  -> Chrome headless bootstrap request 실행
  -> 같은 Chrome profile로 second request 실행
  -> server JSON, Chrome NetLog, qlog 수집
```

인증서 모드:

| 변수 | 의미 |
| --- | --- |
| `CERT_MODE=self-signed` | openssl self-signed certificate 생성 |
| `CERT_MODE=mkcert` | mkcert local CA로 certificate 생성 |
| `CERT_MODE=provided` | `PROVIDED_CERT_FILE`, `PROVIDED_KEY_FILE` 사용 |
| `CHROME_USE_SPKI_EXCEPTION=0` | Chrome SPKI exception flag를 넣지 않음 |

성공 기준:

- server request 중 TCP bootstrap `HTTP/1.1` request가 있어야 한다.
- server request 중 `HTTP/3` request가 있어야 한다.
- target NetLog에 confirmed `QUIC_SESSION`이 있어야 한다.
- qlog에 `http3:frame` evidence가 있어야 한다.

classifier:

- `tools/classify_chrome_alt_svc_artifacts.py`

현재 local control에서는 binary-response 실험이 `alt_svc_advertised_but_h3_not_observed`, self-signed HTML diagnostic이 `alt_svc_quic_candidate_cert_rejected`, mkcert localhost diagnostic이 `alt_svc_marked_broken_without_h3_request`로 분류됐다.

## 10. Chrome public WebPKI H3 discovery baseline

script:

- `repro/quic-go-min-repro/scripts/run-chrome-public-h3.sh`

목적:

local self-signed/mkcert origin이 아니라 public trusted certificate를 가진 origin에서 Chrome이 forced QUIC 없이 H3 discovery 후보를 만드는지 확인한다. 이 실험은 migration 실험이 아니며, application request가 HTTP/3로 처리됐는지는 discovery job과 별도 기준으로 판정한다.

흐름:

```text
public HTTPS target URL 선택
  -> Chrome headless bootstrap navigation
  -> 같은 profile로 second navigation
  -> bootstrap/second NetLog 저장
  -> target host 기준 QUIC_SESSION, dns_alpn_h3 discovery job, application using_quic job, Alt-Svc broken state 분류
```

classifier:

- `tools/classify_chrome_public_h3_artifacts.py`

주요 classification:

| classification | 의미 |
| --- | --- |
| `public_natural_h3_observed` | public origin에서 forced QUIC 없이 target application HTTP/3 사용이 관찰됨 |
| `public_h3_discovery_without_application_h3` | H3 discovery 또는 QUIC session 단서는 있으나 application/main request의 HTTP/3 사용은 확인되지 않음 |
| `public_alt_svc_marked_broken` | target alternative service가 broken으로 기록됨 |
| `public_alt_svc_or_request_observed_but_h3_not_confirmed` | request/Alt-Svc evidence는 있으나 target H3 사용을 확정하지 못함 |

현재 재분류 결과:

- `https://cloudflare-quic.com/cdn-cgi/trace`
- `https://www.google.com/generate_204`
- `https://www.youtube.com/generate_204`

세 endpoint 모두 H3 discovery control로는 유용했지만, artifact 재분류 기준으로 application HTTP/3 evidence는 확보하지 못했다.

## 11. Controlled public WebPKI origin gate

관련 파일:

- `tools/check_public_origin_readiness.py`
- `tools/check_controlled_public_experiment_readiness.py`
- `tools/check_browser_cm_observability.py`
- `tools/classify_controlled_public_h3_baseline.py`
- `tools/classify_controlled_public_h3_network_change.py`
- `tools/capture_network_path_snapshot.py`
- `tools/compare_network_path_snapshots.py`
- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh`
- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh`
- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh`

목적:

연구자가 제어하는 public DNS/WebPKI origin에서 Chrome application HTTP/3 no-change baseline을 먼저 통과시키기 위한 gate다. 이 gate가 통과한 뒤에만 active network change를 넣는다.

흐름:

```text
DNS/TLS/Alt-Svc readiness check
  -> public h3server with WebPKI cert/key
  -> Chrome bootstrap/second navigation
  -> NetLog classification
  -> server request log + qlog + NetLog combined classification
```

최종 application H3 gate:

| evidence | 기준 |
| --- | --- |
| server request log | expected request count 이상 도달 |
| server qlog | `chosen_alpn > 0` and `http3_frame > 0` |
| Chrome NetLog | application `using_quic` job이 있으면 강한 browser-side evidence, 없으면 server qlog로 보완 |
| readiness | DNS/TLS/HTTPS와 `Alt-Svc: h3` 확인 |

주요 classification:

| classification | 의미 |
| --- | --- |
| `controlled_public_application_h3_confirmed` | server/qlog와 browser NetLog가 모두 application H3를 지지 |
| `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive` | server/qlog는 application H3를 직접 증명하지만 browser NetLog는 discovery 수준 |
| `controlled_public_h3_discovery_without_server_application_h3` | browser discovery는 있으나 server/qlog application H3가 없음 |
| `controlled_public_application_h3_not_confirmed` | application H3 evidence 부족 |

### 11.1 Controlled public network-change gate

application H3 baseline summary가 `status=PASS`인 경우에만 active network-change 실험으로 넘어간다.

readiness gate:

```text
public origin readiness
  + application H3 baseline summary
  + active secondary path
  + NETWORK_CHANGE_CMD
  -> can_run_network_change
```

추가 흐름:

```text
baseline PASS summary 확인
  -> long-running browser workload 실행
  -> NETWORK_CHANGE_CMD 실행
  -> server remote tuple + server qlog path validation + Chrome NetLog 분류
```

주요 classification:

| classification | 의미 |
| --- | --- |
| `possible_connection_migration` | tuple change + qlog path validation + single-session 계열 evidence |
| `reconnect_or_multiple_sessions` | tuple change는 있으나 여러 QUIC session evidence |
| `tuple_changed_without_path_validation` | tuple change는 있으나 path validation 없음 |
| `no_path_change_after_trigger` | network-change command는 실행됐지만 tuple 변화 없음 |

## 12. 실행 예시

### 12.1 Local QUIC transport

```bash
cd repro/quic-go-min-repro
./scripts/run-local-happy-path.sh
```

### 12.2 Local HTTP/3 post-migration workload

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
```

### 12.3 Local HTTP/3 mid-flight workload

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

### 12.4 Chrome local HTTP/3 baseline

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
WORKLOAD=slow SLOW_DURATION_MS=8000 SLOW_CHUNKS=8 RUN_ID=chrome-h3-slow-nochange-check ./scripts/run-chrome-h3-local.sh
LISTEN_ADDR=0.0.0.0:4443 ORIGIN_ADDR="$(ipconfig getifaddr en0):4443" WORKLOAD=slow RUN_ID=chrome-h3-slow-wifi-ip-nochange ./scripts/run-chrome-h3-local.sh
WORKLOAD=poll NETWORK_CHANGE_AFTER_SECONDS=2 NETWORK_CHANGE_CMD='...' RUN_ID=chrome-h3-poll-network-change ./scripts/run-chrome-h3-local.sh
```

### 12.5 Chrome natural Alt-Svc control

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-alt-svc-local-20260624 ./scripts/run-chrome-h3-alt-svc.sh
RUN_ID=chrome-h3-alt-svc-localhost-20260624 ADDR=localhost:4443 LISTEN_ADDR=127.0.0.1:4443 TCP_ADDR=127.0.0.1:4443 ./scripts/run-chrome-h3-alt-svc.sh
```

### 12.6 Chrome public H3 discovery baseline

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-public-h3-cloudflare-quic-trace-20260624 TARGET_URL=https://cloudflare-quic.com/cdn-cgi/trace ./scripts/run-chrome-public-h3.sh
RUN_ID=chrome-public-h3-google-generate204-20260624 TARGET_URL=https://www.google.com/generate_204 ./scripts/run-chrome-public-h3.sh
```

### 12.7 Controlled public H3 origin gate

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/path/fullchain.pem \
TLS_KEY_FILE=/path/privkey.pem \
./scripts/run-controlled-public-h3-server.sh

RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

최종 판정 파일:

- `artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json`

### 12.8 Controlled public H3 network-change

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=handover-slow' \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD='...' \
./scripts/run-controlled-public-h3-network-change.sh
```

최종 판정 파일:

- `artifacts/controlled-public-h3-network-change-001/results/controlled-public-h3-network-change-summary.json`

### 12.9 AWS NLB transport

```bash
WORKLOAD=transport \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 12.10 AWS NLB HTTP/3 post-migration

```bash
WORKLOAD=h3 \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 12.11 AWS NLB HTTP/3 mid-flight upload

```bash
WORKLOAD=h3-midflight-upload \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

### 12.12 AWS NLB HTTP/3 mid-flight download

```bash
WORKLOAD=h3-midflight-download \
NLB_PROTOCOL=TCP_QUIC \
PORT=443 \
PAYLOAD_BYTES=1048576 \
CLIENT_START_DELAY_SECONDS=8 \
./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

## 13. 검증 명령

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

## 14. 공개 repo에서 제외한 것

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
