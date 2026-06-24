# Safari controlled public H3 baseline harness

작성일: 2026-06-24

## 1. 목적

Safari를 Chrome과 같은 browser-level HTTP/3 Connection Migration 실험 대상으로 확장하기 전에, controlled public WebPKI origin에서 Safari가 workload를 요청하고 server/qlog 기반 application H3 evidence를 남길 수 있는지 확인하는 baseline harness를 추가했다.

이 단계는 아직 Safari handover 결과가 아니다. Safari는 Chrome NetLog와 같은 browser-internal artifact가 없으므로, server request log, server qlog, client path snapshot, packet capture를 중심으로 별도 evidence chain을 구성해야 한다.

## 2. 추가한 파일

- `tools/run_safari_webdriver_navigation.py`
- `repro/quic-go-min-repro/scripts/run-safari-controlled-public-baseline.sh`

## 3. 실행 전제

필수 조건:

| 항목 | 의미 |
| --- | --- |
| controlled public origin | DNS/WebPKI/TCP 443/UDP 443/Alt-Svc 준비 |
| Safari WebDriver | `safaridriver --version` 성공 |
| server artifact | `run-controlled-public-h3-server.sh`가 server request/qlog를 기록 |
| classifier mode | `--allow-missing-browser-summary` 사용 |

## 4. 실행 예시

server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=safari-controlled-public-h3-baseline-001 \
ARTIFACT_DIR=artifacts/safari-controlled-public-h3-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Safari side:

```bash
cd repro/quic-go-min-repro
RUN_ID=safari-controlled-public-h3-baseline-001 \
ARTIFACT_DIR=artifacts/safari-controlled-public-h3-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/safari-controlled-public-h3-baseline-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=safari-public-slow' \
SAFARI_WAIT_SECONDS=8 \
./scripts/run-safari-controlled-public-baseline.sh
```

## 5. 결과 파일

```text
results/public-origin-readiness.json
results/safari-navigation.json
results/client-path-before.json
results/client-path-after.json
results/client-path-change-summary.json
results/safari-controlled-public-h3-baseline-summary.json
logs/safaridriver.log
```

## 6. 판정 기준

Safari baseline에서는 Chrome NetLog evidence가 없으므로 `classify_controlled_public_h3_baseline.py --allow-missing-browser-summary`를 사용한다.

허용 가능한 baseline 결과:

| status | classification | 해석 |
| --- | --- | --- |
| `PASS_FEASIBILITY` | `controlled_public_server_qlog_h3_confirmed_browser_summary_missing` | server/qlog는 application H3를 증명하지만 browser 내부 summary는 없음 |
| `PASS` | `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive` | browser summary가 있어도 확정적이지 않고 server/qlog가 주 근거 |

실패 또는 negative control:

| classification | 해석 |
| --- | --- |
| `controlled_public_application_h3_not_confirmed` | server/qlog application H3 evidence 없음 |
| `controlled_public_server_workload_failed` | Safari navigation 후 expected request count 미달 |

## 7. 논문상 의미

Safari는 Chrome과 같은 NetLog 기반 내부 QUIC session evidence를 제공하지 않으므로, Chrome 결과와 동일한 observability level로 비교하면 안 된다.

따라서 Safari 실험은 다음처럼 별도 표기를 둔다.

```text
browser = Safari
observability = server-qlog + client-path-snapshot + optional packet-capture
browser-internal-quic-log = unavailable in current harness
```

이 baseline이 통과한 뒤에만 Safari real interface-change 실험으로 넘어간다.
