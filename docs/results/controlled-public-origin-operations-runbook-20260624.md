# Controlled public origin operations runbook

작성일: 2026-06-24

## 1. 목적

controlled public Chrome HTTP/3 connection migration 실험은 세 조건을 먼저 만족해야 한다.

1. 연구자가 제어하는 public WebPKI origin이 있어야 한다.
2. network-change 이전 no-change application H3 baseline이 `PASS`여야 한다.
3. client 쪽에서 실제 active path를 바꾸는 command와 secondary path가 준비되어야 한다.

이 문서는 위 조건을 사람이 반복 가능하게 맞추기 위한 운영 runbook이다.

## 2. Local config

먼저 local-only 설정 파일을 만든다.

```bash
cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env
```

수정해야 할 값:

| 변수 | 의미 |
| --- | --- |
| `PUBLIC_ORIGIN_HOST` | DNS가 public server를 가리키는 hostname |
| `PUBLIC_ORIGIN_URL` | no-change baseline workload URL |
| `PUBLIC_ORIGIN_NETWORK_CHANGE_URL` | long-running network-change workload URL |
| `TLS_CERT_FILE`, `TLS_KEY_FILE` | WebPKI certificate chain과 private key 경로 |
| `CONTROLLED_PUBLIC_BASELINE_SUMMARY` | baseline PASS summary JSON 경로 |
| `NETWORK_CHANGE_CMD` | 사용자가 명시적으로 허용한 active path change command |

이 파일은 `.gitignore` 대상이다. 실제 private key, domain-specific command, 계정 정보는 commit하지 않는다.

## 3. Public origin 준비

server host에서 필요한 조건:

| 항목 | 요구사항 |
| --- | --- |
| DNS | `PUBLIC_ORIGIN_HOST`가 server public IP로 해석되어야 함 |
| Firewall/security group | TCP 443과 UDP 443 inbound 허용 |
| Certificate | Chrome이 신뢰하는 WebPKI certificate와 hostname match |
| Server process | quic-go `h3server`가 UDP H3와 TCP HTTPS Alt-Svc bootstrap을 함께 제공 |
| Alt-Svc | HTTPS response에 `Alt-Svc: h3=":443"; ma=60`류 header 포함 |

server 실행:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

server process는 expected request count를 채우거나 timeout이 될 때까지 foreground로 유지된다.

## 4. Preflight

client machine에서 다음을 실행한다.

```bash
bash harness/scripts/controlled-public-preflight.sh
```

이 스크립트는 network-change를 실행하지 않는다. 다음만 수행한다.

- local config 로드
- Chrome, Python, curl 존재 확인
- public origin DNS/TLS/HTTPS/Alt-Svc readiness 확인
- baseline summary가 `status=PASS`인지 확인
- active secondary IPv4 path와 `NETWORK_CHANGE_CMD` 존재 여부 확인
- ignored artifact directory에 JSON/Markdown readiness 파일 생성

출력 artifact:

```text
repro/quic-go-min-repro/artifacts/controlled-public-preflight-*/results/
├── controlled-public-experiment-readiness.json
└── controlled-public-experiment-readiness.md
```

## 5. No-change application H3 baseline

preflight에서 public origin reachability가 확인되면 browser baseline을 실행한다.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-h3-application-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-h3-application-baseline-001 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
CHROME_TIMEOUT_SECONDS=20 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

성공 기준:

| 항목 | 기준 |
| --- | --- |
| summary status | `PASS` |
| allowed classification | `controlled_public_application_h3_confirmed` 또는 `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive` |
| server request log | workload request가 expected count 이상 |
| server qlog | `chosen_alpn=h3`와 HTTP/3 frame evidence |
| Chrome NetLog | 있으면 application H3 evidence, 없으면 server/qlog evidence로 보완 |

이 baseline이 실패하면 network-change 실험으로 넘어가지 않는다.

## 6. Controlled network-change run

baseline summary가 `PASS`이고 preflight의 `can_run_network_change=true`가 된 뒤 실행한다.

server side:

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

browser/network side:

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

`NETWORK_CHANGE_CMD`는 실험자가 장비 상태를 확인한 뒤 직접 넣는다. 이 저장소는 임의의 interface down/up command를 자동 생성하지 않는다.

## 7. 판정 규칙

network-change 결과는 다음 파일로 판정한다.

```text
artifacts/controlled-public-h3-network-change-001/results/controlled-public-h3-network-change-summary.json
```

client 쪽 active path 변화는 다음 파일에 별도로 남는다.

```text
artifacts/controlled-public-h3-network-change-001/results/client-path-change-summary.json
```

핵심 classification:

| classification | 해석 |
| --- | --- |
| `possible_connection_migration` | server tuple change와 qlog path validation이 함께 관찰됨 |
| `reconnect_or_multiple_sessions` | tuple change가 있으나 여러 QUIC session evidence가 있어 migration 단정 불가 |
| `tuple_changed_without_path_validation` | tuple은 바뀌었지만 QUIC path validation evidence 부족 |
| `no_path_change_after_trigger` | command 실행 후에도 server 관점 path 변화 없음 |
| `controlled_public_network_change_application_h3_precondition_failed` | baseline/application H3 조건 미충족 |

client path-change summary의 핵심 classification:

| classification | 해석 |
| --- | --- |
| `client_active_path_changed` | client route/interface/gateway/public IP 중 active path 변화 관찰 |
| `interface_set_changed_without_route_change` | interface 목록은 바뀌었지만 target/default route 변화는 없음 |
| `no_client_path_change_observed` | command 전후 client route 관점 변화 없음 |
| `path_snapshot_missing` | before/after snapshot이 없어 client-side path evidence 부족 |

논문에서는 `possible_connection_migration`만을 browser-level CM 후보 성공으로 다룬다. 나머지는 각각 reconnect, no-op, precondition failure로 분리한다.

## 8. 논문상 의미

이 runbook은 “Chrome에서 CM이 됐다/안 됐다”를 성급히 말하지 않기 위한 통제 장치다.

특히 다음 overclaim을 막는다.

- H3 Alt-Svc 광고만 보고 application H3라고 주장
- public endpoint discovery evidence만 보고 workload continuity라고 주장
- inactive interface toggle을 실제 handover라고 주장
- baseline H3 실패를 connection migration 실패라고 주장

최종 browser handover 실험은 이 runbook을 통과한 뒤에만 논문 본 실험으로 채택한다.
