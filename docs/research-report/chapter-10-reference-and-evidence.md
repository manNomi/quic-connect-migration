# Chapter 10 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 10 "Upload Workload Recovery"의 실제 구현 코드, scanner/classifier trigger, 원본 결과, 공식 reference link를 정리한다. 공개 안전성을 위해 concrete origin hostname, public IP address, local network address, SSH target, certificate/private-key path, AWS account/instance 식별자는 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| H3 upload workload server | [h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | `/browser-upload`, `/upload-sink`, streaming request body, DOM outcome 구현 |
| AWS controlled public Chrome trial wrapper | [run-aws-controlled-public-chrome-trial.sh](../../harness/scripts/run-aws-controlled-public-chrome-trial.sh) | public server 실행, local Chrome active/no-change run, validation report 생성 |
| active public H3 network-change runner | [run-controlled-public-h3-network-change.sh](../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh) | page-ready trigger, network-change command, path snapshots, classifier 실행 |
| CDP Chrome runner | [run_chrome_cdp_navigation.js](../../tools/run_chrome_cdp_navigation.js) | ready expression, NetLog, DOM dataset dump 수집 |
| application summary parser | [classify_controlled_public_h3_baseline.py](../../tools/classify_controlled_public_h3_baseline.py) | `uploadComplete`, `uploadError` 등을 application success/failure로 해석 |
| network-change classifier | [classify_controlled_public_h3_network_change.py](../../tools/classify_controlled_public_h3_network_change.py) | server/qlog/NetLog/client path/application evidence 통합 판정 |
| result row drafter | [draft_final_handover_result_row.py](../../tools/draft_final_handover_result_row.py) | upload workload를 CSV row의 task/trigger/failure layer로 변환 |
| local upload summarizer | [summarize_chrome_rebinding_upload_matrix.py](../../tools/summarize_chrome_rebinding_upload_matrix.py) | upload sink bytes, packet rebinding, qlog/NetLog path frame 추출 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-10-scanner-trigger-map-20260630.md](tables/chapter-10-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `h3server/main.go` | `/browser-upload`, request `ReadableStream`, `/upload-sink` bytes | workload가 실제 코드에 존재함 |
| `classify_controlled_public_h3_baseline.py` | `uploadComplete`, terminal `uploadError` | application success/failure를 DOM dataset에서 판단 |
| `classify_controlled_public_h3_network_change.py` | target H3 tuple count, qlog path validation, application outcome | retry success를 CM success로 과장하지 않음 |
| `summarize_chrome_rebinding_upload_matrix.py` | upload sink bytes, qlog/NetLog path frames, proxy packet logs | local proxy control과 public handover를 구분 |
| `validate_final_handover_trial_artifact.py` | claim strength and warnings | negative-control row를 final success로 집계하지 않음 |

## 3. 공식 reference links

| source | 링크 | Chapter 10에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | QUIC path validation과 migration claim boundary |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3 application workload 기준 |
| RFC 9110 | [HTTP Semantics](https://datatracker.ietf.org/doc/html/rfc9110) | HTTP request/response semantics reference |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | server qlog artifact 해석 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog 수집 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | controlled public H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | quic-go qlog 생성 근거 |
| Fetch Standard | [Fetch](https://fetch.spec.whatwg.org/) | browser upload fetch workload 기준 |
| Streams Standard | [Streams](https://streams.spec.whatwg.org/) | `ReadableStream` request body 기준 |
| Chrome DevTools Protocol Page domain | [Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/) | CDP navigation/load event 수집 근거 |
| Chrome DevTools Protocol Runtime domain | [Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) | DOM dataset evaluation 수집 근거 |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/iphone-usb-upload-retry-pilot-20260626.md](../results/iphone-usb-upload-retry-pilot-20260626.md) | Chapter 10 핵심 public upload pilot/replication result |
| [data/iphone-usb-upload-retry-pilot-20260626.csv](../../data/iphone-usb-upload-retry-pilot-20260626.csv) | upload retry rows 원본 CSV. Legacy raw tuple fields가 있으므로 보고서에는 aggregate만 복사 |
| [docs/results/chrome-h3-rebinding-upload-summary-20260624.md](../results/chrome-h3-rebinding-upload-summary-20260624.md) | local upload rebinding control summary |
| [data/chrome-h3-rebinding-upload-summary-20260624.csv](../../data/chrome-h3-rebinding-upload-summary-20260624.csv) | local upload rebinding control CSV |
| [docs/results/chrome-desktop-noniphone-upload-local-refresh-20260630.md](../results/chrome-desktop-noniphone-upload-local-refresh-20260630.md) | fresh non-iPhone Chrome desktop upload local control |
| [data/chrome-desktop-noniphone-upload-local-refresh-20260630.csv](../../data/chrome-desktop-noniphone-upload-local-refresh-20260630.csv) | fresh upload local control CSV |
| [docs/results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md](../results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md) | local transient upload boundary |
| [docs/results/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.md](../results/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.md) | local upload retry boundary |
| [docs/results/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.md](../results/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.md) | local upload retry=2 long outage result |

## 5. Reproducibility Commands

Representative public upload active trial shape:

```bash
TRIAL_ID=controlled-public-chrome-upload-retry-network-change-page-ready-YYYYMMDD-001 \
VARIANT=noheartbeat \
MODE=network-change \
TARGET_URL="$PUBLIC_ORIGIN_URL/browser-upload?duration_ms=16000&chunks=16&bytes=65536&retry_attempts=1&retry_delay_ms=500" \
NETWORK_CHANGE_READY_EXPR="Number(document.body.dataset.uploadBytes || 0) >= 16384" \
NETWORK_CHANGE_CMD="$LOCAL_NETWORK_CHANGE_COMMAND" \
harness/scripts/run-aws-controlled-public-chrome-trial.sh
```

Representative local upload control shape:

```bash
cd repro/quic-go-min-repro
WORKLOAD=upload \
UPLOAD_DURATION_MS=6000 \
UPLOAD_CHUNKS=6 \
UPLOAD_BYTES=262144 \
UPLOAD_RETRY_ATTEMPTS=0 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

실제 host, public IP, local interface name, credential, SSH target은 local ignored config와 raw artifacts에만 있어야 한다.

## 6. Verification Commands

실행한 코드 검증:

```bash
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_baseline.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_network_change.py
PYTHONPATH=tools python3 tools/test_draft_final_handover_result_row.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_upload_matrix.py
```

결과:

| test | result |
| --- | --- |
| `test_classify_controlled_public_h3_baseline.py` | PASS, exit 0 |
| `test_classify_controlled_public_h3_network_change.py` | `classify_controlled_public_h3_network_change=ok` |
| `test_draft_final_handover_result_row.py` | `draft_final_handover_result_row=ok` |
| `test_summarize_chrome_rebinding_upload_matrix.py` | `summarize_chrome_rebinding_upload_matrix=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Upload retry restored user-visible task completion in the matched long public upload repetitions, but the successful rows showed replacement or multiple-session behavior rather than proven Chrome single-session QUIC Connection Migration.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| upload retry success proves CM | successful retry rows used retry and showed multiple target sessions or tuple-only evidence. |
| local upload rebinding equals public handover | local proxy control has no real client route change. |
| qlog path validation alone proves Chrome CM | qlog path validation must be paired with single target session and target tuple evidence. |
| 2026-06-29 fresh upload failed row supports the main claim | server artifact was missing, so it is diagnostic only. |
