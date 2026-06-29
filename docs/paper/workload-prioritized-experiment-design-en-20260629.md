# Workload-Prioritized Experiment Design

Generated: `2026-06-29`

## Core Decision

Streaming is important for a Connection Migration study, but the paper should not treat playback completion as transport-layer success. QUIC CM is transport continuity. Web task continuity is also shaped by retry, Range resume, segment fetches, buffer depth, replacement sessions, and CDN/proxy termination.

The safest experiment order is therefore:

1. Large upload/download, because interruption maps directly to user-task failure.
2. Range/resumable download, because full retry and partial retry are different recovery semantics.
3. Live or low-latency video, because small buffers expose disruption as rebuffering.
4. Video on demand, because larger buffers can hide transport disruption.
5. Music-like streaming, because lower bitrate and larger effective buffers make it useful as a low-sensitivity control.

## Existing Evidence

| workload | primary result | CM evidence | paper use |
| --- | --- | --- | --- |
| large_upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Strongest user-task continuity case; upload failure maps directly to task failure |
| large_download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Shows HTTP/3 alone did not preserve long response, while app recovery can be full-retry or resumable-range recovery |
| polling_dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Useful for dashboard/workflow freshness but requires page-ready public rerun |
| media_segments | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Shows streaming continuity can be preserved while hiding transport CM gaps, and must be measured with startup/rebuffer metrics |
| music_like_buffered | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Use as application-recovery control showing streaming continuity depends on retry/buffer policy |

## Streaming And Large-Transfer Case Split

| case | priority | network pattern | next experiment | interpretation risk |
| --- | --- | --- | --- | --- |
| Large upload | 1 | long-lived client-to-server body | Repeat page-ready public handover with retry0 and retry1 | Retry success can be reconnect/multiple-session recovery rather than QUIC CM |
| Large download | 2 | long-lived server-to-client body | Repeat page-ready public handover with timeout-only and retry-enabled download | Range or fetch retry can hide missing single-session migration |
| Live or low-latency video | 3 | small segments with tight timing and low buffer | Run media segments with short interval and page-ready handover after first segment | Segment retry may preserve playback semantics without proving QUIC CM |
| Video on demand | 4 | small segments with larger buffer | Run media segments with larger interval/buffer and compare no-retry vs retry | Buffering makes user-visible failure less likely even when transport migrates poorly |
| Music streaming | 5 | small low-bitrate segments with larger effective buffer | Use smaller bytes and longer interval as a low-sensitivity control | Audio may be too tolerant and should be framed as a low-sensitivity negative/control workload |

## Next Experiment Matrix

| experiment | priority | workload | minimum runs | claim unlocked |
| --- | --- | --- | --- | --- |
| P0-fresh-public-h3-baseline | 0 | baseline | 1 PASS | public origin is ready for active handover rows |
| P1-downlink-noheartbeat-active | 1 | large_download/downlink | 3 | strongest browser CM positive or negative row for long downlink |
| P1-downlink-heartbeat-active | 2 | large_download/downlink | 3 | separates active client probing/application traffic from true single-session CM |
| P2-upload-retry-boundary-public | 3 | large_upload | 3 per variant | application recovery benefit and session-continuity cost for user-generated content upload |
| P2-range-download-public | 4 | large_download/range | 3 per variant | resumable transfer design guidance for HTTP/3 workloads |
| P3-buffered-media-public | 5 | video/music streaming | 3 per profile | QoE-aware streaming continuity result without overclaiming CM |
| P4-safari-feasibility | 6 | browser feasibility | 1 | cross-browser feasibility row with weaker browser-internal observability |
| P4-android-chrome-feasibility | 7 | mobile browser feasibility | 1 | true mobile-platform feasibility beyond Mac+iPhone tethered failover |

## Hypotheses

- H1: During active Wi-Fi-to-iPhone-USB failover, Chrome may not reliably preserve a long upload/downlink as a single HTTP/3 QUIC session without application recovery.
- H2: retry, Range resume, and segment retry can improve task completion while increasing session churn and completion latency.
- H3: buffered media can complete even when transport CM is absent or unproven; the paper should report startup delay, rebuffering, retry, and session churn rather than only completion.
- H4: low-latency video should be more sensitive than VOD/music, but bitrate alone is not enough to predict sensitivity; the current music-like no-retry control failed under a 6000 ms disruption.

## Evidence Ladder

| level | meaning | required evidence | paper wording |
| --- | --- | --- | --- |
| L0 | HTTP/3 capability | Alt-Svc or Chrome NetLog application H3 | H3 baseline |
| L1 | task continuity | DOM completion or upload/download/media complete | the task completed |
| L2 | path-change continuity | client path snapshot plus server tuple/qlog change | task completion during path change |
| L3 | single-session browser CM | L2 plus one Chrome target QUIC session and qlog path validation | browser single-session CM evidence |
| L4 | workload/QoE impact | L3 or L2 plus latency/rebuffer/retry/session churn | workload-specific user impact |

## Classification Rules

- Upload/download rows must report task completion, retry count, received bytes, completion latency, and Chrome session count.
- Range rows must separate whole-response retry from byte-range recovery.
- Media rows must include startup delay, rebuffer events, fetched/played segment counts, and retry counts.
- Third-party public sites are only H3 discovery/control evidence. Without server qlog and tuple evidence they cannot support CM success claims.
- The iPhone USB trigger should be named `latent Wi-Fi-loss-to-iPhone-USB cellular failover`, not simultaneous active multipath.

## Why Not Start With Streaming Only

Streaming is user-important, but buffering and segment retry can hide transport failure. Starting with streaming alone risks confusing playback completion with CM success. A stronger paper first establishes the transport continuity gap with upload/download, then uses streaming to show application recovery and QoE tradeoffs.

## Source Anchors

- RFC 9000 for QUIC connection migration and path validation. <https://datatracker.ietf.org/doc/html/rfc9000>
- RFC 9114 for HTTP/3 as an HTTP mapping over QUIC, without application recovery guarantees. <https://datatracker.ietf.org/doc/html/rfc9114>
- ACM CCR 2025 `An Analysis of QUIC Connection Migration in the Wild` for deployment/wild-measurement boundaries. <https://dl.acm.org/doi/10.1145/3727063.3727066>
- IETF Media over QUIC WG for emerging QUIC-based media delivery, kept separate from this study's browser HTTP/3 segment-fetch model. <https://datatracker.ietf.org/wg/moq/about/>

## Next Execution

The immediate external dependency is public-origin recovery. Once it is reachable, run `P0 -> P1 no-heartbeat -> P1 heartbeat -> P2 upload/range -> P3 buffered media -> P4 Safari/Android`.

Regenerate with: `python3 tools/build_workload_prioritized_experiment_design.py`
