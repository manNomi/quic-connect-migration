# Chapter 6 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 6 "Local Chrome NAT Rebinding Control"의 실제 구현 코드, 실험 script, scanner/classifier trigger, 원본 결과, 공식 reference link를 정리한다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| UDP rebinding proxy | [repro/quic-go-min-repro/cmd/udprebindproxy/main.go](../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go) | upstream A/B socket, switch-after, A/B server packet drop 구현 |
| local Chrome rebinding runner | [repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh) | server/proxy/Chrome 실행, NetLog/DOM/qlog/proxy artifact 생성 |
| repetition matrix runner | [repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh) | heartbeat/no-heartbeat 반복 matrix |
| return-path drop runner | [repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-return-path-drop-controls.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-return-path-drop-controls.sh) | B-only drop과 A+B drop negative control |
| transient outage runner | [repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh) | bounded A+B return-path outage sweep |
| boundary repetition runner | [repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-boundary-repetition.sh) | 4000/4500/5000ms 반복 boundary |
| H3 server | [repro/quic-go-min-repro/cmd/h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | qlog, request log, browser workload endpoint |
| Chrome classifier | [tools/classify_chrome_h3_artifacts.py](../../tools/classify_chrome_h3_artifacts.py) | NetLog/qlog/proxy/DOM/server artifact 통합 판정 |
| timing summarizer | [tools/summarize_chrome_rebinding_timing_sensitivity.py](../../tools/summarize_chrome_rebinding_timing_sensitivity.py) | early/late switch timing summary 생성 |
| transient summarizer | [tools/summarize_chrome_rebinding_transient_return_path_sweep.py](../../tools/summarize_chrome_rebinding_transient_return_path_sweep.py) | transient outage boundary summary 생성 |
| fresh non-iPhone media result | [docs/results/chrome-desktop-noniphone-media-local-refresh-20260630.md](../results/chrome-desktop-noniphone-media-local-refresh-20260630.md) | Chrome desktop local media positive control, public handover 아님 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-06-scanner-trigger-map-20260630.md](tables/chapter-06-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `udprebindproxy` | `switch-after` 이후 upstream B 사용, A/B server packet drop option | packet-level rebinding과 real client path change를 구분 |
| `run-chrome-h3-rebinding-proxy.sh` | server/proxy/Chrome artifact 생성 후 classifier 실행 | runner는 판정하지 않고 classifier summary를 생성 |
| `classify_chrome_h3_artifacts.py` | server request, NetLog, qlog, proxy switched, DOM completion | application failure와 multiple session을 PASS로 과장하지 않음 |
| summarizers | proxy JSONL, summary JSON, DOM attributes, qlog counts, upload bytes | aggregated table과 raw artifact 경로를 같이 남김 |

## 3. 공식 reference links

| source | 링크 | Chapter 6에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | NAT rebinding, connection migration, path validation 기준 |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | application HTTP/3 request/workload 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | qlog artifact 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog artifact 생성 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session/path event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | quic-go H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | quic-go qlog 생성 근거 |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/chrome-h3-rebinding-repetition-summary-20260624.md](../results/chrome-h3-rebinding-repetition-summary-20260624.md) | heartbeat/no-heartbeat local rebinding 6회 반복 요약 |
| [data/chrome-h3-rebinding-repetition-summary-20260624.csv](../../data/chrome-h3-rebinding-repetition-summary-20260624.csv) | repetition summary CSV |
| [docs/results/chrome-h3-rebinding-timing-sensitivity-20260624.md](../results/chrome-h3-rebinding-timing-sensitivity-20260624.md) | early/late rebinding timing sensitivity |
| [data/chrome-h3-rebinding-timing-sensitivity-20260624.csv](../../data/chrome-h3-rebinding-timing-sensitivity-20260624.csv) | timing sensitivity CSV |
| [docs/results/chrome-h3-rebinding-old-path-drop-20260624.md](../results/chrome-h3-rebinding-old-path-drop-20260624.md) | old return path drop control |
| [data/chrome-h3-rebinding-old-path-drop-20260624.csv](../../data/chrome-h3-rebinding-old-path-drop-20260624.csv) | old-path drop CSV |
| [docs/results/chrome-h3-rebinding-return-path-drop-controls-20260624.md](../results/chrome-h3-rebinding-return-path-drop-controls-20260624.md) | B-only / A+B return-path drop controls |
| [data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv](../../data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv) | return-path drop CSV |
| [docs/results/chrome-h3-rebinding-transient-return-path-sweep-20260624.md](../results/chrome-h3-rebinding-transient-return-path-sweep-20260624.md) | transient outage broad sweep |
| [data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv](../../data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv) | transient broad sweep CSV |
| [docs/results/chrome-h3-rebinding-transient-boundary-repetition-20260624.md](../results/chrome-h3-rebinding-transient-boundary-repetition-20260624.md) | 4000/4500/5000ms repeated boundary |
| [data/chrome-h3-rebinding-transient-boundary-repetition-20260624.csv](../../data/chrome-h3-rebinding-transient-boundary-repetition-20260624.csv) | boundary repetition CSV |
| [docs/results/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.md](../results/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.md) | downlink 5000/5500/6000ms fine boundary |
| [data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv](../../data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv) | downlink fine CSV |
| [docs/results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md](../results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md) | upload 4600/4750/4900/5000ms fine boundary |
| [data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv](../../data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv) | upload fine CSV |
| [docs/results/chrome-desktop-noniphone-media-local-refresh-20260630.md](../results/chrome-desktop-noniphone-media-local-refresh-20260630.md) | fresh non-iPhone Chrome desktop media local control |
| [data/chrome-desktop-noniphone-media-local-refresh-20260630.csv](../../data/chrome-desktop-noniphone-media-local-refresh-20260630.csv) | fresh media local control CSV |

## 5. Reproducibility Commands

대표 단일 run:

```bash
cd repro/quic-go-min-repro
RUN_ID=chapter6-local-rebinding-smoke \
WORKLOAD=downlink \
REBIND_AFTER=2s \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

repetition matrix:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chapter6-rebinding-matrix \
./scripts/run-chrome-h3-rebinding-proxy-matrix.sh
```

return-path drop controls:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chapter6-return-path-drop \
./scripts/run-chrome-h3-rebinding-return-path-drop-controls.sh
```

transient outage sweep:

```bash
cd repro/quic-go-min-repro
MATRIX_ID=chapter6-transient-sweep \
./scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh
```

## 6. Verification Commands

실행한 코드 검증:

```bash
cd repro/quic-go-min-repro
go test ./cmd/udprebindproxy ./cmd/h3server
```

```bash
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_old_path_drop.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_timing_sensitivity.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_return_path_drop_controls.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_transient_return_path_sweep.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_upload_matrix.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_stress_matrix.py
```

결과:

| test | result |
| --- | --- |
| `go test ./cmd/udprebindproxy ./cmd/h3server` | PASS |
| `test_summarize_chrome_rebinding_old_path_drop.py` | `summarize_chrome_rebinding_old_path_drop=ok` |
| `test_summarize_chrome_rebinding_timing_sensitivity.py` | `summarize_chrome_rebinding_timing_sensitivity=ok` |
| `test_summarize_chrome_rebinding_return_path_drop_controls.py` | `summarize_chrome_rebinding_return_path_drop_controls=ok` |
| `test_summarize_chrome_rebinding_transient_return_path_sweep.py` | `summarize_chrome_rebinding_transient_return_path_sweep=ok` |
| `test_summarize_chrome_rebinding_upload_matrix.py` | `summarize_chrome_rebinding_upload_matrix=ok` |
| `test_summarize_chrome_rebinding_stress_matrix.py` | `summarize_chrome_rebinding_stress_matrix=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Local Chrome forced-H3 NAT rebinding controls provide repeatable evidence for packet rebinding, qlog path validation, Chrome NetLog path-validation frames, and DOM-level workload success/failure.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| 실제 Wi-Fi/LTE handover success | local proxy control에는 client route/interface/public-IP change가 없다. |
| single-session browser CM success in all rows | heartbeat/retry row는 multiple QUIC sessions를 만들 수 있다. |
| transport path validation guarantees web task continuity | return-path drop failure row가 반례다. |
