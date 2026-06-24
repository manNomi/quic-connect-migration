# Controlled public Chrome H3 network-change harness

작성일: 2026-06-24

## 1. 목적

controlled public application H3 gate가 통과한 뒤, 같은 public WebPKI origin에서 Chrome workload 실행 중 active network/interface change를 넣고 결과를 분류하기 위한 하네스를 추가했다.

이 단계는 아직 실제 handover 결과가 아니다. 실제 실행에는 public domain, WebPKI certificate, UDP/TCP 443, active secondary network가 필요하다.

## 2. 추가한 파일

- `repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh`
- `tools/classify_controlled_public_h3_network_change.py`

## 3. 실행 전제

먼저 controlled public application H3 baseline이 통과해야 한다.

필수 precondition:

```text
controlled-public-h3-baseline-summary.json
  status = PASS
```

이 파일은 `run-controlled-public-h3-browser-baseline.sh`와 `classify_controlled_public_h3_baseline.py`가 만든다.

## 4. 실행 흐름

```text
baseline PASS summary 확인
  -> public origin readiness check
  -> Chrome headless navigation to long-running workload
  -> NETWORK_CHANGE_AFTER_SECONDS 뒤 NETWORK_CHANGE_CMD 실행
  -> Chrome NetLog, network-change JSON, server request log, server qlog 수집
  -> controlled-public-h3-network-change-summary.json 생성
```

## 5. 예시

Server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Browser/network side:

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

`NETWORK_CHANGE_CMD`에는 실제 active path를 바꾸는 명령을 넣는다. 예를 들어 macOS에서는 Wi-Fi/LTE tethering, route priority, 또는 특정 network service toggle을 별도로 설계해야 한다. inactive interface toggle은 이전 실험에서 migration evidence를 만들지 못했으므로 실제 active path change로 보지 않는다.

## 6. 판정 기준

결과 파일:

```text
results/controlled-public-h3-network-change-summary.json
```

주요 classification:

| classification | 의미 |
| --- | --- |
| `possible_connection_migration` | server remote tuple change + server qlog path validation + 단일/불명확하지 않은 QUIC session evidence |
| `reconnect_or_multiple_sessions` | tuple change와 path validation은 있으나 browser NetLog상 여러 QUIC session이 관찰됨 |
| `tuple_changed_without_path_validation` | server tuple은 바뀌었지만 QUIC path validation evidence가 없음 |
| `path_validation_without_observed_tuple_change` | path validation은 있으나 server request remote tuple 변화가 없음 |
| `no_path_change_after_trigger` | network-change command는 실행됐지만 server remote tuple 변화가 없음 |
| `controlled_public_network_change_workload_failed` | workload가 expected request count에 도달하지 못함 |
| `controlled_public_network_change_application_h3_precondition_failed` | server/qlog application H3 evidence가 없음 |

## 7. 논문상 의미

이 하네스는 connection migration의 성패를 단순히 Chrome NetLog 하나로 판단하지 않도록 만든다.

최소 evidence chain:

1. controlled public application H3 baseline PASS
2. active network-change command 실행 성공
3. server request log의 remote tuple 변화 여부
4. server qlog의 PATH_CHALLENGE/PATH_RESPONSE 여부
5. Chrome NetLog의 QUIC session/reconnect 단서

이 다섯 가지를 함께 봐야 browser-level HTTP/3 Connection Migration과 단순 reconnect를 분리할 수 있다.
