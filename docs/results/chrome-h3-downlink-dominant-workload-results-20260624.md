# Chrome H3 downlink-dominant workload results

작성일: 2026-06-24

## 1. 목적

브라우저 Connection Migration 실험에서 단순 upload/download baseline만 사용하면, client가 path change 직후 새 path에서 packet을 얼마나 빨리 보내는지 분리하기 어렵다.

따라서 Chrome forced-QUIC local H3 baseline에 다음 두 workload를 추가했다.

| workload | 목적 |
| --- | --- |
| downlink without heartbeat | server가 streaming response를 보내는 동안 browser가 추가 request를 만들지 않는 client-silent에 가까운 조건 확인 |
| downlink with heartbeat | streaming response 중 application-level small fetch가 추가 client packet/request evidence를 만드는지 확인 |

이 문서는 migration 성공 결과가 아니라, 실제 active path-change 실험 전에 workload와 classifier가 정상 동작하는지 확인한 baseline 결과다.

## 2. 구현 변경

server:

- `GET /browser-downlink`: browser HTML/JS page 생성
- `GET /downlink-stream`: chunk delay가 있는 binary streaming response
- `GET /heartbeat`: optional application heartbeat JSON response

wrapper:

- `run-chrome-h3-local.sh`에 `WORKLOAD=downlink` 추가
- `DOWNLINK_HEARTBEAT=false`이면 expected request count는 2
- `DOWNLINK_HEARTBEAT=true`이면 expected request count는 3

## 3. 실험 환경

| 항목 | 값 |
| --- | --- |
| date | 2026-06-24 |
| browser | Chrome 149 headless |
| server | quic-go HTTP/3 server |
| origin mode | local forced QUIC origin |
| TLS | ephemeral local test certificate + SPKI exception |
| classifier | `tools/classify_chrome_h3_artifacts.py` |
| migration trigger | 없음 |

## 4. 실행 1: no-heartbeat baseline

command:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=false \
CHROME_TIMEOUT_SECONDS=12 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
RUN_ID=chrome-h3-downlink-noheartbeat-20260624 \
./scripts/run-chrome-h3-local.sh
```

artifact:

```text
repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-20260624
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| classification | `no_path_change_baseline` |
| expected requests | 2 |
| server request count | 2 |
| server paths | `/browser-downlink`, `/downlink-stream` |
| server remote addr count | 1 |
| Chrome target QUIC session count | 1 |
| Chrome target `using_quic=true` job count | 2 |
| qlog `http3:frame` count | 9 |
| qlog path validation | false |

해석:

- Chrome browser가 downlink streaming workload를 HTTP/3로 수행했다.
- path 변화가 없었으므로 tuple change와 PATH_CHALLENGE/PATH_RESPONSE가 없는 것이 정상이다.
- Chrome NetLog의 `QUIC_CONNECTION_MIGRATION_MODE` 문자열은 migration 발생 근거가 아니라 설정/모드 evidence로만 해석한다.

## 5. 실행 2: heartbeat baseline

command:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=400 \
CHROME_TIMEOUT_SECONDS=12 \
CHROME_VIRTUAL_TIME_BUDGET_MS=3000 \
ADDR=127.0.0.1:4453 \
LISTEN_ADDR=127.0.0.1:4453 \
ORIGIN_ADDR=127.0.0.1:4453 \
RUN_ID=chrome-h3-downlink-heartbeat-20260624-rerun \
./scripts/run-chrome-h3-local.sh
```

artifact:

```text
repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624-rerun
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| classification | `no_path_change_baseline` |
| expected requests | 3 |
| server request count | 3 |
| server paths | `/browser-downlink`, `/downlink-stream`, `/heartbeat` |
| server remote addr count | 1 |
| Chrome target QUIC session count | 1 |
| Chrome target `using_quic=true` job count | 3 |
| qlog `http3:frame` count | 11 |
| qlog path validation | false |

해석:

- heartbeat variant도 동일한 local H3 evidence chain에서 관찰됐다.
- heartbeat request는 streaming response 중 별도 application request를 만들기 때문에, 실제 active path-change 실험에서는 post-change client packet/request를 유도하는 recovery variant로 사용할 수 있다.
- 이 실행도 path change가 없으므로 migration evidence는 없어야 정상이다.

## 6. 논문에 주는 의미

이번 단계로 논문 실험 설계에 다음 비교축을 추가할 수 있다.

| 비교축 | 질문 |
| --- | --- |
| downlink silent | server-to-client traffic만 계속되는 동안 path change가 생기면 browser/server가 언제 새 path를 인지하는가 |
| downlink + heartbeat | application heartbeat가 post-change recovery 또는 migration detection을 앞당기는가 |
| polling interval | periodic request 간격이 길수록 failure/recovery detection이 늦어지는가 |

아직 결론낼 수 없는 것:

- 실제 Wi-Fi/LTE 또는 active interface handover에서 Chrome이 QUIC Connection Migration을 수행하는지
- public WebPKI controlled origin에서 natural browser H3가 같은 결과를 보이는지
- Safari가 동일 workload를 HTTP/3로 처리하고 같은 recovery 특성을 보이는지

따라서 다음 단계는 controlled public origin에서 `WORKLOAD=downlink`와 active path-change trigger를 결합하고, `client-path-change-summary.json`, server remote tuple, qlog path validation, Chrome NetLog를 함께 판정하는 것이다.

## 7. CDP real-time runner 추가 검수

`--dump-dom` 기반 Chrome runner는 virtual time과 page 종료 시점의 영향을 받는다. 특히 `DOWNLINK_HEARTBEAT=true`에서 heartbeat timer가 실제 시간 기준으로 언제 실행되는지 안정적으로 통제하기 어렵다.

이를 보완하기 위해 `tools/run_chrome_cdp_navigation.js`를 추가했다. 이 runner는 Chrome DevTools Protocol로 page를 열고, 지정한 real-time hold 구간 동안 page를 유지한 뒤 DOM과 body dataset을 수집한다.

wrapper:

```bash
CHROME_RUNNER=cdp CHROME_HOLD_SECONDS=4 ./scripts/run-chrome-h3-local.sh
```

또한 downlink workload는 expected request count가 stream 완료 전에 먼저 채워질 수 있으므로, `run-chrome-h3-local.sh`가 `COMPLETION_GRACE`를 기본적으로 `DOWNLINK_DURATION_MS + 1000ms`로 설정하도록 보강했다.

### 7.1 CDP no-heartbeat no-change

command:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=false \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=4 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
ADDR=127.0.0.1:4466 \
LISTEN_ADDR=127.0.0.1:4466 \
ORIGIN_ADDR=127.0.0.1:4466 \
RUN_ID=chrome-h3-downlink-noheartbeat-cdp-nochange-20260624 \
./scripts/run-chrome-h3-local.sh
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| classification | `no_path_change_baseline` |
| server request count | 2 |
| server remote addr count | 1 |
| Chrome target QUIC session count | 1 |
| Chrome target `using_quic=true` job count | 2 |
| qlog path validation | false |

### 7.2 CDP heartbeat no-change

command:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=1200 \
DOWNLINK_CHUNKS=3 \
DOWNLINK_BYTES=4096 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=400 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=4 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
ADDR=127.0.0.1:4465 \
LISTEN_ADDR=127.0.0.1:4465 \
ORIGIN_ADDR=127.0.0.1:4465 \
RUN_ID=chrome-h3-downlink-heartbeat-cdp-nochange-grace-20260624 \
./scripts/run-chrome-h3-local.sh
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| classification | `multiple_quic_sessions_without_network_change` |
| server request count | 3 |
| server remote addr count | 2 |
| Chrome target QUIC session count | 2 |
| Chrome target `using_quic=true` job count | 3 |
| qlog path validation | false |
| page dataset | `heartbeatStatus=200`, `downlinkComplete=true` |

해석:

- network-change trigger가 없어도 heartbeat fetch가 별도 QUIC session/source port로 갈 수 있다.
- 따라서 server remote tuple 변화만으로 Connection Migration을 주장하면 안 된다.
- 최소한 qlog path validation과 browser NetLog의 session count를 함께 봐야 한다.

### 7.3 CDP heartbeat + inactive interface toggle

command:

```bash
cd repro/quic-go-min-repro
WORKLOAD=downlink \
DOWNLINK_DURATION_MS=8000 \
DOWNLINK_CHUNKS=8 \
DOWNLINK_BYTES=8192 \
DOWNLINK_HEARTBEAT=true \
DOWNLINK_HEARTBEAT_DELAY_MS=3000 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=11 \
CHROME_TIMEOUT_SECONDS=25 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
ADDR=127.0.0.1:4467 \
LISTEN_ADDR=127.0.0.1:4467 \
ORIGIN_ADDR=127.0.0.1:4467 \
RUN_ID=chrome-h3-downlink-heartbeat-cdp-inactive-if-toggle-20260624 \
./scripts/run-chrome-h3-local.sh
```

result:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| classification | `multiple_quic_sessions_without_client_path_change` |
| network change exit | 0 |
| client path classification | `no_client_path_change_observed` |
| active interface before/after | `en0` -> `en0` |
| target route before/after | `lo0` -> `lo0` |
| server request count | 3 |
| server remote addr count | 2 |
| Chrome target QUIC session count | 2 |
| NetLog migration event class | `mode=4`, trigger/success/failure 없음 |
| qlog path validation | false |
| page dataset | `heartbeatStatus=200`, `downlinkComplete=true` |

해석:

- inactive interface toggle은 command 자체는 성공하지만 active client path를 바꾸지 않는다.
- heartbeat request 때문에 server remote addr와 QUIC session은 2개가 될 수 있다.
- client path snapshot이 없었다면 이 결과를 reconnect나 migration처럼 오해할 수 있다.
- NetLog의 migration 관련 문자열은 `QUIC_CONNECTION_MIGRATION_MODE`뿐이었고, 실제 trigger/success/failure event는 관찰되지 않았다.
- 이 대조군은 논문에서 “CM evidence chain은 tuple change 단독이 아니라 client path change, qlog path validation, browser session evidence를 함께 요구해야 한다”는 근거로 사용할 수 있다.
