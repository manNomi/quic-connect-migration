# Chapter 8 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 8 "Full-Response Downlink Public Handover"의 실제 구현 코드, scanner/classifier trigger, 원본 결과, 공식 reference link를 정리한다. 공개 안전성을 위해 concrete origin hostname, public IP address, local network address, SSH target, certificate/private-key path, AWS account/instance 식별자는 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| active public H3 network-change runner | [run-controlled-public-h3-network-change.sh](../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh) | public origin readiness, Chrome 실행, network-change command, path snapshot, classifier 실행 |
| final Chrome wrapper | [final-chrome-network-change-run.sh](../../harness/scripts/final-chrome-network-change-run.sh) | config readiness, baseline unlock, network-change runner, postcheck 연결 |
| network-change classifier | [classify_controlled_public_h3_network_change.py](../../tools/classify_controlled_public_h3_network_change.py) | server/qlog/NetLog/client path/application DOM evidence 통합 판정 |
| path snapshot capturer | [capture_network_path_snapshot.py](../../tools/capture_network_path_snapshot.py) | route/interface/public-path snapshot 생성 |
| path snapshot comparator | [compare_network_path_snapshots.py](../../tools/compare_network_path_snapshots.py) | before/after route snapshot을 `client_active_path_changed` 등으로 분류 |
| CDP Chrome runner | [run_chrome_cdp_navigation.js](../../tools/run_chrome_cdp_navigation.js) | page-ready trigger, Chrome NetLog, DOM dataset dump 수집 |
| H3 workload server | [h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | `/browser-downlink`, `/downlink-stream`, DOM dataset outcome 구현 |
| result row drafter | [draft_final_handover_result_row.py](../../tools/draft_final_handover_result_row.py) | classifier summary를 `experiment-results.csv` shape로 변환 |
| artifact validator | [validate_final_handover_trial_artifact.py](../../tools/validate_final_handover_trial_artifact.py) | negative control, final-countable 여부, warning 생성 |
| artifact bundle checker | [check_final_handover_trial_artifact_bundle.py](../../tools/check_final_handover_trial_artifact_bundle.py) | expected artifact presence와 final-countability 검수 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-08-scanner-trigger-map-20260630.md](tables/chapter-08-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `run-controlled-public-h3-network-change.sh` | baseline gate, readiness, page-ready network command, before/after path snapshots | runner는 판정하지 않고 classifier summary를 생성 |
| `capture_network_path_snapshot.py` | target route, default route, active IPv4 interfaces, optional public IP probe | client path change를 artifact로 남김 |
| `compare_network_path_snapshots.py` | default/target interface/gateway/public IP change | mere interface-set change와 active path change를 구분 |
| `classify_controlled_public_h3_network_change.py` | server H3/qlog, Chrome NetLog, network command, client path change, DOM application outcome | application failure와 missing qlog path validation을 CM success로 과장하지 않음 |
| `validate_final_handover_trial_artifact.py` | final requirement match, status, application_success | negative-control row를 final success로 집계하지 않음 |
| `h3server/main.go` | `/browser-downlink` HTML and `/downlink-stream` body | workload가 실제 코드에 존재함을 확인 |

## 3. 공식 reference links

| source | 링크 | Chapter 8에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | QUIC path validation과 migration claim boundary |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3 application workload 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | server qlog artifact 해석 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog 수집 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | controlled public H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | quic-go qlog 생성 근거 |
| Fetch Standard | [Fetch](https://fetch.spec.whatwg.org/) | browser fetch workload와 response body 관찰 기준 |
| Streams Standard | [Streams](https://streams.spec.whatwg.org/) | `ReadableStream` reader 기반 downlink workload 기준 |
| Chrome DevTools Protocol Page domain | [Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/) | CDP navigation/load event 수집 근거 |
| Chrome DevTools Protocol Runtime domain | [Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) | DOM dataset evaluation 수집 근거 |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md](../results/controlled-public-full-downlink-iphone-usb-handover-20260629.md) | Chapter 8 핵심 결과 보고서 |
| [docs/results/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001-validation.md](../results/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001-validation.md) | no-change baseline validation |
| [docs/results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001-validation.md](../results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001-validation.md) | active trial 001 validation |
| [docs/results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002-validation.md](../results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002-validation.md) | active trial 002 validation |
| [docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md](../results/controlled-public-range-retry-iphone-usb-handover-20260629.md) | byte-range retry 비교 결과 |

Raw artifacts are intentionally ignored by git:

| artifact | 의미 |
| --- | --- |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` | no-change browser artifact |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001-server` | no-change server qlog/request artifact |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001` | active browser artifact 001 |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001-server` | active server qlog/request artifact 001 |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002` | active browser artifact 002 |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002-server` | active server qlog/request artifact 002 |

## 5. Reproducibility Commands

대표 active trial shape:

```bash
TRIAL_ID=controlled-public-chrome-downlink-full-network-change-page-ready-fresh-YYYYMMDD-001 \
PUBLIC_ORIGIN_NETWORK_CHANGE_URL="$PUBLIC_ORIGIN_URL/browser-downlink?duration_ms=15000&chunks=15&retry_attempts=0" \
NETWORK_CHANGE_READY_EXPR="Number(document.body.dataset.downlinkBytes || 0) > 0" \
NETWORK_CHANGE_CMD="$LOCAL_NETWORK_CHANGE_COMMAND" \
harness/scripts/final-chrome-network-change-run.sh
```

직접 runner를 호출하는 shape:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-full-network-change-page-ready-fresh-YYYYMMDD-001 \
PUBLIC_ORIGIN_URL="$PUBLIC_ORIGIN_URL/browser-downlink?duration_ms=15000&chunks=15&retry_attempts=0" \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR="artifacts/<server-artifact>" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="artifacts/<baseline>/results/controlled-public-h3-baseline-summary.json" \
NETWORK_CHANGE_READY_EXPR="Number(document.body.dataset.downlinkBytes || 0) > 0" \
NETWORK_CHANGE_CMD="$LOCAL_NETWORK_CHANGE_COMMAND" \
CHROME_RUNNER=cdp \
./scripts/run-controlled-public-h3-network-change.sh
```

Validation shape:

```bash
PYTHONPATH=tools python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-downlink-full-network-change-page-ready-fresh-YYYYMMDD-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-YYYYMMDD-001 \
  --format markdown
```

실제 host, public IP, local interface name, credential, SSH target은 local ignored config와 raw artifacts에만 있어야 한다.

## 6. Verification Commands

실행한 코드 검증:

```bash
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_network_change.py
PYTHONPATH=tools python3 tools/test_validate_final_handover_trial_artifact.py
PYTHONPATH=tools python3 tools/test_check_final_handover_trial_artifact_bundle.py
PYTHONPATH=tools python3 tools/test_draft_final_handover_result_row.py
PYTHONPATH=tools python3 tools/test_final_chrome_network_change_run_wrapper.py
```

결과:

| test | result |
| --- | --- |
| `test_classify_controlled_public_h3_network_change.py` | PASS, exit 0 |
| `test_validate_final_handover_trial_artifact.py` | `validate_final_handover_trial_artifact=ok` |
| `test_check_final_handover_trial_artifact_bundle.py` | `check_final_handover_trial_artifact_bundle=ok` |
| `test_draft_final_handover_result_row.py` | `draft_final_handover_result_row=ok` |
| `test_final_chrome_network_change_run_wrapper.py` | `final_chrome_network_change_run_wrapper=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> The full-response downlink workload failed in two active Chrome Wi-Fi to iPhone USB path-change trials, while no server qlog path-validation evidence was observed.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| Chrome QUIC CM success | qlog path validation이 없고 application success도 false다. |
| Chrome QUIC CM global failure | current trial shape에 대한 negative result일 뿐이다. |
| application retry proves CM | byte-range retry success는 application recovery evidence이지 same-connection migration evidence가 아니다. |
| raw network-change command is public reproducibility data | command may expose local network configuration, so report only command shape. |
