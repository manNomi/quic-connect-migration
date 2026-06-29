# Streaming And Large-Transfer Workload Case Analysis (2026-06-29)

## Purpose

The next research chapter should not treat all web tasks as equal. QUIC Connection Migration matters most when an address/path change interrupts an in-progress user task. The current evidence already shows strong behavior differences between upload, downlink, polling, and application-level retry. This chapter extends the harness toward streaming-style workloads.

## Direction

Recommended priority:

1. Large upload
2. Large download
3. Live or low-latency video
4. Video on demand
5. Music streaming

The reason is workload sensitivity. Upload and long download are naturally vulnerable to a single transfer failure. Media playback often uses segmented fetches and buffering, so application behavior can hide transport migration failure. This makes media useful, but it must be framed differently from upload/download.

## Harness Update

Added a media-segment workload:

- `GET /browser-media-segments`
- `GET /media-segment`

The browser page sequentially fetches segment-like binary objects and records:

- `mediaCompletedCount`
- `mediaRetriesUsed`
- `mediaBytes`
- `mediaElapsedMs`
- `mediaComplete`
- `mediaLastError`
- `mediaError`
- `mediaErrorElapsedMs`

The classifier now recognizes `media*` body dataset keys as workload `media`. Controlled public network-change classification also treats `browser-media-segments` and `media-segment` as target H3 workloads.

This is intentionally a segment-fetch model, not a codec/decoder test. It models the network behavior shared by VOD, live video, and music streaming while avoiding browser codec and media pipeline differences.

## Local Smoke Result

| field | value |
| --- | --- |
| artifact | `repro/quic-go-min-repro/artifacts/chrome-h3-media-segment-smoke-20260629` |
| workload | `WORKLOAD=media` |
| page | `/browser-media-segments?count=3&interval_ms=100&bytes=4096&segment_duration_ms=50&segment_chunks=2` |
| expected requests | `4` |
| server result | `ok=true`, `4/4 requests` |
| browser application result | `mediaComplete=true`, `mediaCompletedCount=3`, `mediaRetriesUsed=0` |
| browser protocol result | Chrome used HTTP/3 for the page and all segment fetches |
| local classifier | `PASS`, `multiple_quic_sessions_without_network_change` |

Important caveat: even without network change, this short segment workload used two Chrome target QUIC sessions / two local source ports. This is useful evidence for the paper because segment-style media workloads can naturally involve multiple sessions. Therefore, media task completion must not be interpreted as single-session QUIC Connection Migration unless session attribution, server tuple change, client path change, and qlog path validation align.

## Local Rebinding Pilot

The first transient return-path pilot was added in `docs/results/chrome-h3-rebinding-media-segment-pilot-20260629.md`.

Summary:

- 500ms, 1500ms, 3000ms, and 6000ms local A+B return-path drop windows all completed.
- All rows used `MEDIA_RETRY_ATTEMPTS=0`.
- All rows were classified as `nat_rebinding_multiple_quic_sessions`.
- The 6000ms row completed with three target Chrome QUIC sessions and a duplicate segment request.

This strengthens the workload-dependent framing: media segment continuity can survive disruption, but the observed mechanism is not single-session browser CM.

## Local Rebinding Replication

Replication artifacts:

- `docs/results/chrome-h3-rebinding-media-segment-replication-20260629.md`
- `docs/results/chrome-h3-rebinding-music-like-media-control-20260629.md`
- `docs/results/chrome-h3-rebinding-buffered-media-control-20260629.md`

Video-like segment profile:

| drop window | retry | PASS/runs | media complete | Chrome sessions | classification |
| --- | ---: | ---: | ---: | --- | --- |
| 3000ms | 0 | 3/3 | 3/3 | 2-2 | `nat_rebinding_multiple_quic_sessions` |
| 6000ms | 0 | 3/3 | 3/3 | 2-3 | `nat_rebinding_multiple_quic_sessions` |

Music-like smaller-segment profile:

| drop window | retry | PASS/runs | media complete | Chrome sessions | classification |
| --- | ---: | ---: | ---: | --- | --- |
| 6000ms | 0 | 0/3 | 0/3 | 2-2 | `browser_h3_request_failed` |
| 6000ms | 1 | 3/3 | 3/3 | 3-3 | `nat_rebinding_multiple_quic_sessions` |

The replication changes the earlier expectation: smaller or lower-bitrate segment fetches are not automatically tolerant. The no-retry music-like profile repeatedly failed after the first segment under the same 6000ms return-path loss. One retry recovered visible completion, but the observed mechanism was still multiple Chrome QUIC sessions rather than single-session CM.

Buffered playback profile:

| drop window | retry | startup/max buffer | PASS/runs | playback complete | startup/rebuffer result | classification |
| --- | ---: | --- | ---: | ---: | --- | --- |
| 3000ms | 0 | 1/1 | 3/3 | 3/3 | fast startup, 14 rebuffer events each | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 0 | 4/6 | 3/3 | 3/3 | ~15s startup, 0 rebuffer events | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 2 | 1/1 | 3/3 | 3/3 | fast startup, 3-14 rebuffer events | `nat_rebinding_multiple_quic_sessions` |
| 3000ms | 2 | 4/6 | 3/3 | 3/3 | ~15s startup, 0 rebuffer events | `nat_rebinding_multiple_quic_sessions` |

This adds an important paper point: streaming continuity is not a binary task-completion result. Buffer depth can trade startup delay against rebuffering, while the underlying browser behavior is still replacement/multiple-session continuity rather than single-session QUIC CM.

## Next Public Handover Trials

Use the page-ready trigger added in `docs/results/page-ready-network-change-runner-20260629.md`.

For live/low-latency video-like workload:

```bash
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.mediaCompletedCount || "0") >= 1'
PUBLIC_ORIGIN_URL='https://43-203-244-29.sslip.io/browser-media-segments?count=8&interval_ms=250&bytes=32768&segment_duration_ms=100&segment_chunks=2&retry_attempts=0&retry_delay_ms=500&label=public-media-live'
```

For retry-enabled live/low-latency video-like workload:

```bash
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.mediaCompletedCount || "0") >= 1'
PUBLIC_ORIGIN_URL='https://43-203-244-29.sslip.io/browser-media-segments?count=8&interval_ms=250&bytes=32768&segment_duration_ms=100&segment_chunks=2&retry_attempts=2&retry_delay_ms=500&label=public-media-live-retry2'
```

For VOD/music-like lower-sensitivity controls:

```bash
PUBLIC_ORIGIN_URL='https://43-203-244-29.sslip.io/browser-media-segments?count=6&interval_ms=1000&bytes=8192&segment_duration_ms=0&segment_chunks=1&retry_attempts=2&retry_delay_ms=500&label=public-media-buffered-retry2'
```

## Paper Framing

The expected contribution is not simply "CM helps streaming." A more defensible claim is:

> QUIC CM relevance is workload-dependent. Long-lived upload/download tasks expose transport continuity more directly, while media workloads often convert transport disruption into segment retry, buffer depletion, quality adaptation, or reconnect behavior. Therefore browser HTTP/3 CM maturity should be evaluated together with workload semantics and application recovery strategy.

Related large-transfer control:

- `docs/results/chrome-h3-rebinding-range-download-control-20260629.md`

This Range/resume control is not a streaming workload, but it helps separate two recovery semantics that matter for video/file transfer: restarting a whole long response versus retrying only the failed byte range.

## Data

- Workload case matrix: `data/streaming-workload-case-analysis-20260629.csv`
- Workload sensitivity matrix: `data/workload-sensitivity-synthesis-20260629.csv`
- Local smoke artifact: `repro/quic-go-min-repro/artifacts/chrome-h3-media-segment-smoke-20260629`
