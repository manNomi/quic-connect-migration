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
