# Safari controlled public H3 network-change harness

작성일: 2026-06-24

## 1. 목적

Safari에서 controlled public WebPKI origin을 대상으로 long-running HTTP/3 workload 실행 중 active network/interface change를 넣는 wrapper를 추가했다.

이 단계는 아직 Safari handover 결과가 아니다. 현재 장비에는 active secondary path가 없으므로, 이번 결과는 실행 가능한 harness와 판정 기준을 준비한 것이다.

## 2. 추가한 파일

- `repro/quic-go-min-repro/scripts/run-safari-controlled-public-network-change.sh`
- `tools/classify_controlled_public_h3_network_change.py`의 `--browser-kind safari` mode

## 3. 실행 전제

필수 precondition:

```text
Safari 또는 controlled-public baseline summary
  status starts with PASS

controlled public origin
  DNS/WebPKI/TCP 443/UDP 443/Alt-Svc 준비

active network-change command
  command 전후 client path snapshot에서 실제 active path 변화가 관찰되어야 함
```

Safari는 Chrome NetLog와 같은 browser-internal QUIC session artifact를 제공하지 않으므로, `--browser-kind safari --allow-missing-browser-netlog`로 server/qlog/client-path 중심의 evidence chain을 만든다.

## 4. 실행 예시

Server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=safari-controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/safari-controlled-public-h3-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Safari/network side:

```bash
cd repro/quic-go-min-repro
RUN_ID=safari-controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/safari-controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/safari-controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/safari-controlled-public-h3-baseline-001/results/safari-controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=safari-handover-slow' \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD='...' \
SAFARI_WAIT_SECONDS=18 \
./scripts/run-safari-controlled-public-network-change.sh
```

## 5. 결과 파일

```text
results/public-origin-readiness.json
results/safari-navigation.json
results/network-change.json
results/client-path-before.json
results/client-path-command-before.json
results/client-path-command-after.json
results/client-path-change-summary.json
results/client-path-final.json
results/safari-controlled-public-h3-network-change-summary.json
logs/network-change.log
logs/safaridriver.log
```

## 6. 판정 기준

Safari network-change summary에서 새로 사용하는 classification:

| classification | status | 의미 |
| --- | --- | --- |
| `possible_connection_migration_server_qlog_only` | `PASS_FEASIBILITY` | server remote tuple change와 qlog path validation은 있지만 browser-internal QUIC session evidence가 없음 |
| `tuple_changed_without_path_validation` | `PASS_NEGATIVE_CONTROL` | tuple은 바뀌었지만 QUIC path validation evidence 없음 |
| `no_path_change_after_trigger` | `PASS_NEGATIVE_CONTROL` | network-change command 후에도 server tuple 변화 없음 |
| `controlled_public_network_change_workload_failed` | `FAIL` | Safari workload가 expected request count에 도달하지 못함 |

client path-change summary는 Chrome harness와 동일하게 해석한다.

| client classification | 의미 |
| --- | --- |
| `client_active_path_changed` | command 전후 active route/interface/gateway/public IP 변화 관찰 |
| `interface_set_changed_without_route_change` | interface 목록은 바뀌었지만 target/default route 변화 없음 |
| `no_client_path_change_observed` | command가 실제 active path를 바꾸지 못함 |

## 7. 논문상 의미

Safari 결과는 Chrome 결과와 같은 관찰성 레벨로 비교하면 안 된다.

논문 표기:

```text
browser = Safari
evidence = server request log + server qlog + client path snapshot + optional packet capture
browser-internal-quic-log = unavailable
claim strength = feasibility unless packet capture or vendor-internal logs add stronger evidence
```

따라서 Safari에서 `possible_connection_migration_server_qlog_only`가 나오더라도, 논문에서는 "Safari에서 browser-internal evidence까지 확보한 CM 성공"이 아니라 "server/qlog 관점에서 CM-compatible behavior가 관찰됨"으로 써야 한다.
