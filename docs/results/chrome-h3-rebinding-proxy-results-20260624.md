# Chrome H3 Local UDP Rebinding Proxy Results

작성일: 2026-06-24

## 1. 목적

이 실험은 public Wi-Fi/LTE handover를 대체하지 않는다. 대신 Chrome forced-QUIC HTTP/3 traffic 앞에 local UDP rebinding proxy를 두고, proxy가 upstream UDP socket을 바꿀 때 server-side qlog와 browser NetLog가 어떤 증거를 남기는지 확인한다.

핵심 질문은 다음이다.

> server tuple change와 qlog path validation만으로 browser Connection Migration 성공을 주장할 수 있는가?

결론부터 말하면, 현재 결과는 "아니다"에 가깝다. qlog path validation과 request 성공은 관찰됐지만, heartbeat 조건에서 Chrome NetLog가 target QUIC session 2개를 보여 session continuity claim은 보수적으로 막아야 한다.

## 2. 구현

추가된 실행 요소:

| 파일 | 역할 |
| --- | --- |
| `repro/quic-go-min-repro/cmd/udprebindproxy/main.go` | client-facing UDP address와 server-facing UDP socket A/B를 가진 local rebinding proxy |
| `repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh` | quic-go H3 server, UDP rebinding proxy, Chrome CDP navigation을 묶는 wrapper |

구조:

```text
Chrome
  -> 127.0.0.1:proxy-port
  -> UDP rebinding proxy
  -> upstream socket A, then B
  -> quic-go HTTP/3 server
```

switch 기준은 proxy 시작 시간이 아니라 첫 client packet 이후 `REBIND_AFTER`다.

## 3. 실행 1: no heartbeat

command:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-rebinding-noheartbeat-smoke-20260624 \
ARTIFACT_DIR=artifacts/chrome-h3-rebinding-noheartbeat-smoke-20260624 \
PROXY_ADDR=127.0.0.1:4547 \
SERVER_ADDR=127.0.0.1:4548 \
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=6000 \
DOWNLINK_CHUNKS=6 \
DOWNLINK_BYTES=32768 \
DOWNLINK_HEARTBEAT=false \
REBIND_AFTER=2s \
TIMEOUT=25s \
CHROME_TIMEOUT_SECONDS=20 \
CHROME_HOLD_SECONDS=10 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| experiment CSV status | PASS_FEASIBILITY |
| classifier | `nat_rebinding_path_validation_without_observed_tuple_change` |
| expected requests | 2 |
| server request count | 2 |
| server request remote addr count | 1 |
| proxy switched | true |
| proxy upstream | `127.0.0.1:58046 -> 127.0.0.1:49564` |
| Chrome target QUIC sessions | 1 |
| Chrome using_quic jobs | 2 |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 1 / 1 |
| application success | yes |

해석:

- proxy는 실제로 upstream socket을 바꿨고 qlog path validation도 관찰됐다.
- 그러나 post-rebind application request가 없어서 request-level `remote_addr`는 하나로 남았다.
- 따라서 이 행은 browser active handover evidence가 아니라 local NAT-rebinding feasibility evidence다.

## 4. 실행 2: heartbeat

command:

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-rebinding-heartbeat-smoke2-20260624 \
ARTIFACT_DIR=artifacts/chrome-h3-rebinding-heartbeat-smoke2-20260624 \
PROXY_ADDR=127.0.0.1:4545 \
SERVER_ADDR=127.0.0.1:4546 \
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=6000 \
DOWNLINK_CHUNKS=6 \
DOWNLINK_BYTES=32768 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=3000 \
REBIND_AFTER=2s \
TIMEOUT=25s \
CHROME_TIMEOUT_SECONDS=20 \
CHROME_HOLD_SECONDS=10 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| experiment CSV status | PASS_NEGATIVE_CONTROL |
| classifier | `nat_rebinding_multiple_quic_sessions` |
| expected requests | 3 |
| server request count | 3 |
| server request remote addr count | 2 |
| proxy switched | true |
| proxy upstream | `127.0.0.1:49851 -> 127.0.0.1:56349` |
| Chrome target QUIC sessions | 2 |
| Chrome using_quic jobs | 3 |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 1 / 1 |
| application success | yes |

해석:

- heartbeat fetch 이후 server request remote tuple이 바뀌었다.
- qlog path validation도 관찰됐다.
- 하지만 Chrome NetLog상 target QUIC session이 2개라서, 이 결과만으로 browser session continuity를 주장하면 안 된다.

## 5. 논문에서의 사용

사용 가능한 주장:

- local UDP rebinding proxy로 Chrome HTTP/3 workload에서 server-side path validation을 유도할 수 있다.
- request success, tuple change, qlog path validation이 모두 있어도 browser session continuity artifact가 따로 필요하다.
- heartbeat는 post-rebind request evidence를 만들지만 replacement/multiple-session 가능성도 함께 만든다.

아직 주장하면 안 되는 것:

- Chrome이 실제 Wi-Fi/LTE handover에서 connection migration에 성공했다.
- Chrome이 단일 QUIC session을 유지했다.
- 이 결과가 public controlled-origin final protocol row를 대체한다.
