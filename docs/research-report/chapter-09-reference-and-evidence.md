# Chapter 9 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 9 "Byte-Range Download And Retry Recovery"의 실제 구현 코드, scanner/classifier trigger, 원본 결과, 공식 reference link를 정리한다. 공개 안전성을 위해 concrete origin hostname, public IP address, local network address, SSH target, certificate/private-key path, AWS account/instance 식별자는 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| AWS controlled public Chrome trial wrapper | [run-aws-controlled-public-chrome-trial.sh](../../harness/scripts/run-aws-controlled-public-chrome-trial.sh) | remote public H3 server 실행, local Chrome active/no-change run, validation report 생성 |
| active public H3 network-change runner | [run-controlled-public-h3-network-change.sh](../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh) | page-ready trigger, network-change command, path snapshots, classifier 실행 |
| CDP Chrome runner | [run_chrome_cdp_navigation.js](../../tools/run_chrome_cdp_navigation.js) | ready expression, NetLog, DOM dataset dump 수집 |
| H3 range workload server | [h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | `/browser-range-download`, `/range-download`, Range header handling, DOM outcome 구현 |
| application summary parser | [classify_controlled_public_h3_baseline.py](../../tools/classify_controlled_public_h3_baseline.py) | `rangeComplete`, `rangeError` 등을 application success/failure로 해석 |
| network-change classifier | [classify_controlled_public_h3_network_change.py](../../tools/classify_controlled_public_h3_network_change.py) | server/qlog/NetLog/client path/application evidence 통합 판정 |
| result row drafter | [draft_final_handover_result_row.py](../../tools/draft_final_handover_result_row.py) | range workload를 CSV row의 task/trigger/failure layer로 변환 |
| artifact validator | [validate_final_handover_trial_artifact.py](../../tools/validate_final_handover_trial_artifact.py) | tuple change without qlog path validation을 CM success에서 제외 |
| local range summarizer | [summarize_chrome_rebinding_range_matrix.py](../../tools/summarize_chrome_rebinding_range_matrix.py) | local range-control artifact에서 range bytes/retry/session/qlog field 추출 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-09-scanner-trigger-map-20260630.md](tables/chapter-09-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `h3server/main.go` | `/browser-range-download`, `/range-download`, `Range` header, DOM `range*` dataset | workload가 실제 코드에 존재함 |
| `classify_controlled_public_h3_baseline.py` | `rangeComplete`, terminal `rangeError` | application success/failure를 DOM dataset에서 직접 판단 |
| `classify_controlled_public_h3_network_change.py` | target H3 tuple count, qlog path validation, application success | tuple change만으로 CM success 처리하지 않음 |
| `validate_final_handover_trial_artifact.py` | claim strength and warnings | `tuple_changed_without_path_validation` row를 final success로 집계하지 않음 |
| `draft_final_handover_result_row.py` | workload `range` | task를 byte-range download로 명시 |

## 3. 공식 reference links

| source | 링크 | Chapter 9에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | QUIC path validation과 migration claim boundary |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3 application workload 기준 |
| RFC 9110 Range Requests | [HTTP Semantics: Range Requests](https://datatracker.ietf.org/doc/html/rfc9110#name-range-requests) | HTTP byte-range recovery 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | server qlog artifact 해석 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog 수집 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | controlled public H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | quic-go qlog 생성 근거 |
| Fetch Standard | [Fetch](https://fetch.spec.whatwg.org/) | browser fetch workload 기준 |
| Streams Standard | [Streams](https://streams.spec.whatwg.org/) | response body stream handling 기준 |
| Chrome DevTools Protocol Page domain | [Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/) | CDP navigation/load event 수집 근거 |
| Chrome DevTools Protocol Runtime domain | [Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) | DOM dataset evaluation 수집 근거 |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md](../results/controlled-public-range-retry-iphone-usb-handover-20260629.md) | Chapter 9 핵심 결과 보고서 |
| [docs/results/controlled-public-chrome-range-noretry-nochange-fresh-20260629-001-validation.md](../results/controlled-public-chrome-range-noretry-nochange-fresh-20260629-001-validation.md) | retry=0 no-change validation |
| [docs/results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001-validation.md](../results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001-validation.md) | retry=0 active trial 001 validation |
| [docs/results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002-validation.md](../results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002-validation.md) | retry=0 active trial 002 validation |
| [docs/results/controlled-public-chrome-range-retry-nochange-fresh-20260629-001-validation.md](../results/controlled-public-chrome-range-retry-nochange-fresh-20260629-001-validation.md) | retry=2 no-change validation |
| [docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001-validation.md](../results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001-validation.md) | retry=2 active trial 001 validation |
| [docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002-validation.md](../results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002-validation.md) | retry=2 active trial 002 validation |
| [docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003-validation.md](../results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003-validation.md) | retry=2 active trial 003 validation |
| [docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md](../results/controlled-public-full-downlink-iphone-usb-handover-20260629.md) | full-response downlink 비교 결과 |

Raw artifacts are intentionally ignored by git:

| artifact shape | 의미 |
| --- | --- |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-noretry-nochange-fresh-20260629-001` | retry=0 no-change browser artifact |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-*` | retry=0 active browser artifacts |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-nochange-fresh-20260629-001` | retry=2 no-change browser artifact |
| `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-*` | retry=2 active browser artifacts |
| `repro/quic-go-min-repro/artifacts/*-server` | matched server qlog/request artifacts |

## 5. Reproducibility Commands

대표 retry=2 active trial shape:

```bash
TRIAL_ID=controlled-public-chrome-range-retry-network-change-page-ready-fresh-YYYYMMDD-001 \
VARIANT=noheartbeat \
MODE=network-change \
TARGET_URL="$PUBLIC_ORIGIN_URL/browser-range-download?bytes=524288&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=2&retry_delay_ms=500" \
NETWORK_CHANGE_READY_EXPR="Number(document.body.dataset.rangeCompletedBytes || 0) >= 131072" \
NETWORK_CHANGE_CMD="$LOCAL_NETWORK_CHANGE_COMMAND" \
harness/scripts/run-aws-controlled-public-chrome-trial.sh
```

대표 retry=0 active trial shape:

```bash
TRIAL_ID=controlled-public-chrome-range-noretry-network-change-page-ready-fresh-YYYYMMDD-001 \
VARIANT=noheartbeat \
MODE=network-change \
TARGET_URL="$PUBLIC_ORIGIN_URL/browser-range-download?bytes=524288&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=0&retry_delay_ms=500" \
NETWORK_CHANGE_READY_EXPR="Number(document.body.dataset.rangeCompletedBytes || 0) >= 131072" \
NETWORK_CHANGE_CMD="$LOCAL_NETWORK_CHANGE_COMMAND" \
harness/scripts/run-aws-controlled-public-chrome-trial.sh
```

Validation shape:

```bash
PYTHONPATH=tools python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id controlled-public-chrome-range-retry-network-change-page-ready-fresh-YYYYMMDD-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-YYYYMMDD-001 \
  --format markdown
```

실제 host, public IP, local interface name, credential, SSH target은 local ignored config와 raw artifacts에만 있어야 한다.

## 6. Verification Commands

실행한 코드 검증:

```bash
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_baseline.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_network_change.py
PYTHONPATH=tools python3 tools/test_draft_final_handover_result_row.py
PYTHONPATH=tools python3 tools/test_validate_final_handover_trial_artifact.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_range_matrix.py
```

결과:

| test | result |
| --- | --- |
| `test_classify_controlled_public_h3_baseline.py` | PASS, exit 0 |
| `test_classify_controlled_public_h3_network_change.py` | `classify_controlled_public_h3_network_change=ok` |
| `test_draft_final_handover_result_row.py` | `draft_final_handover_result_row=ok` |
| `test_validate_final_handover_trial_artifact.py` | `validate_final_handover_trial_artifact=ok` |
| `test_summarize_chrome_rebinding_range_matrix.py` | `summarize_chrome_rebinding_range_matrix=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Byte-range retry improved user-visible download completion in the current controlled public Chrome path-change trials, but the rows remain negative controls for browser QUIC Connection Migration because qlog path validation was not observed.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| retry=2 success is CM success | validator warning says tuple change without qlog path validation excludes CM success. |
| tuple count 2 alone proves migration | classifier keeps `tuple_changed_without_path_validation` as `PASS_NEGATIVE_CONTROL`. |
| retry always solves continuity | retry=2 active trial 002 still failed. |
| no-change baseline proves handover | no-change is application H3 baseline only. |
