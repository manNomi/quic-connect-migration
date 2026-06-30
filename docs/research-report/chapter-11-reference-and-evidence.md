# Chapter 11 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 11 "Streaming And Media Workload"의 실제 구현 코드, scanner/classifier trigger, 원본 결과, 공식 reference link를 정리한다. 공개 안전성을 위해 concrete origin hostname, public IP address, local network address, SSH target, certificate/private-key path, AWS account/instance 식별자는 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| H3 media workload server | [h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | `/browser-media-segments`, `/browser-buffered-media`, `/media-segment` 구현 |
| local Chrome rebinding runner | [run-chrome-h3-rebinding-proxy.sh](../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh) | media/range/upload/downlink workload를 local UDP rebinding proxy로 실행 |
| media segment summarizer | [summarize_chrome_rebinding_media_matrix.py](../../tools/summarize_chrome_rebinding_media_matrix.py) | segment count, retry, duplicate segment, sessions, qlog fields 추출 |
| buffered media summarizer | [summarize_chrome_rebinding_buffered_media_matrix.py](../../tools/summarize_chrome_rebinding_buffered_media_matrix.py) | startup/rebuffer/buffer depth/session/qlog fields 추출 |
| application summary parser | [classify_controlled_public_h3_baseline.py](../../tools/classify_controlled_public_h3_baseline.py) | `mediaComplete`, `mediaError` 등을 application success/failure로 해석 |
| network-change classifier | [classify_controlled_public_h3_network_change.py](../../tools/classify_controlled_public_h3_network_change.py) | media workloads를 target H3 workloads로 포함 |
| Chrome artifact classifier | [classify_chrome_h3_artifacts.py](../../tools/classify_chrome_h3_artifacts.py) | local DOM/qlog/NetLog/server/proxy evidence 통합 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-11-scanner-trigger-map-20260630.md](tables/chapter-11-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `h3server/main.go` | media segment and buffered playback DOM datasets | workload가 실제 코드에 존재함 |
| `summarize_chrome_rebinding_media_matrix.py` | `mediaComplete`, duplicate segment count, sessions, qlog | segment completion을 CM success로 과장하지 않음 |
| `summarize_chrome_rebinding_buffered_media_matrix.py` | startup delay, rebuffer events, playback complete | completion-only metric 방지 |
| `classify_controlled_public_h3_baseline.py` | `mediaComplete`, terminal `mediaError` | application success/failure를 DOM dataset에서 판단 |
| `classify_controlled_public_h3_network_change.py` | media target workload list | future public media rows에서 target tuple filtering 가능 |

## 3. 공식 reference links

| source | 링크 | Chapter 11에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | QUIC path validation과 migration claim boundary |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3 application workload 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | server qlog artifact 해석 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog 수집 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | controlled/local H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | quic-go qlog 생성 근거 |
| Fetch Standard | [Fetch](https://fetch.spec.whatwg.org/) | segment fetch workload 기준 |
| Streams Standard | [Streams](https://streams.spec.whatwg.org/) | response stream and body handling 기준 |
| Chrome DevTools Protocol Page domain | [Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/) | CDP navigation/load event 수집 근거 |
| Chrome DevTools Protocol Runtime domain | [Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/) | DOM dataset evaluation 수집 근거 |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/streaming-workload-case-analysis-20260629.md](../results/streaming-workload-case-analysis-20260629.md) | streaming workload 설계와 synthesis |
| [data/streaming-workload-case-analysis-20260629.csv](../../data/streaming-workload-case-analysis-20260629.csv) | streaming workload matrix |
| [docs/results/chrome-h3-rebinding-media-segment-pilot-20260629.md](../results/chrome-h3-rebinding-media-segment-pilot-20260629.md) | initial media segment pilot |
| [docs/results/chrome-h3-rebinding-media-segment-replication-20260629.md](../results/chrome-h3-rebinding-media-segment-replication-20260629.md) | video-like segment replication |
| [data/chrome-h3-rebinding-media-segment-replication-20260629.csv](../../data/chrome-h3-rebinding-media-segment-replication-20260629.csv) | video-like media CSV |
| [docs/results/chrome-h3-rebinding-music-like-media-control-20260629.md](../results/chrome-h3-rebinding-music-like-media-control-20260629.md) | music-like segment control |
| [data/chrome-h3-rebinding-music-like-media-control-20260629.csv](../../data/chrome-h3-rebinding-music-like-media-control-20260629.csv) | music-like media CSV |
| [docs/results/chrome-h3-rebinding-buffered-media-control-20260629.md](../results/chrome-h3-rebinding-buffered-media-control-20260629.md) | buffered playback control |
| [data/chrome-h3-rebinding-buffered-media-control-20260629.csv](../../data/chrome-h3-rebinding-buffered-media-control-20260629.csv) | buffered playback CSV |

## 5. Reproducibility Commands

Representative local media segment control:

```bash
cd repro/quic-go-min-repro
WORKLOAD=media \
MEDIA_SEGMENTS=8 \
MEDIA_INTERVAL_MS=250 \
MEDIA_SEGMENT_BYTES=32768 \
MEDIA_SEGMENT_DURATION_MS=100 \
MEDIA_SEGMENT_CHUNKS=2 \
MEDIA_RETRY_ATTEMPTS=0 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

Representative local buffered media control:

```bash
cd repro/quic-go-min-repro
WORKLOAD=buffered-media \
MEDIA_SEGMENTS=8 \
MEDIA_SEGMENT_BYTES=32768 \
MEDIA_SEGMENT_DURATION_MS=100 \
MEDIA_RETRY_ATTEMPTS=2 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

Future public media handover should use local ignored config values and must not commit concrete public origin URLs, interface names, or network-change commands.

## 6. Verification Commands

실행한 코드 검증:

```bash
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_media_matrix.py
PYTHONPATH=tools python3 tools/test_summarize_chrome_rebinding_buffered_media_matrix.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_baseline.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_network_change.py
```

결과:

| test | result |
| --- | --- |
| `test_summarize_chrome_rebinding_media_matrix.py` | `summarize_chrome_rebinding_media_matrix=ok` |
| `test_summarize_chrome_rebinding_buffered_media_matrix.py` | `summarize_chrome_rebinding_buffered_media_matrix=ok` |
| `test_classify_controlled_public_h3_baseline.py` | PASS, exit 0 |
| `test_classify_controlled_public_h3_network_change.py` | `classify_controlled_public_h3_network_change=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Local streaming-style controls show that playback or segment completion can survive disruption through segmentation, retry, buffering, duplicate fetches, and multiple Chrome QUIC sessions, so media continuity must be evaluated with QoE and session attribution.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| media PASS rows prove browser CM | current media rows are local proxy controls and multiple-session rows. |
| playback complete means no user impact | startup delay and rebuffer events changed substantially. |
| retry is always unnecessary | music-like no-retry rows failed 3/3 under the tested loss window. |
| public handover media is complete | public media handover rows still need to be run and classified. |
