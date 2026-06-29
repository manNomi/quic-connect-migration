# Workload 우선순위 기반 다음 실험 설계

생성일: `2026-06-29`

## 핵심 판단

Connection Migration 연구에서 스트리밍은 중요하다. 다만 논문에서 가장 먼저 증명해야 할 대상은 `동영상이 끝까지 재생됐다`가 아니라, 어떤 계층이 연속성을 만들었는지다. QUIC CM은 transport continuity이고, 브라우저/웹 애플리케이션의 작업 연속성은 retry, Range resume, segment fetch, buffer depth, replacement session, CDN/proxy termination이 함께 만든다.

따라서 실험 우선순위는 다음처럼 잡는 것이 안전하다.

1. 대용량 upload/download: 중단이 사용자 작업 실패로 바로 드러나므로 CM gap을 가장 선명하게 보여준다.
2. Range/resumable download: 같은 download라도 전체 재시도와 부분 재시도를 분리한다.
3. live/low-latency video: buffer가 작아 path disruption이 rebuffer로 드러나기 쉽다.
4. VOD/video-on-demand: buffer가 커서 transport failure가 가려질 수 있으므로 QoE metric이 필요하다.
5. music-like streaming: 낮은 bitrate와 큰 effective buffer 때문에 negative/control workload로 유용하다.

## 기존 증거 요약

| workload | 주요 결과 | CM evidence | 논문 사용 |
| --- | --- | --- | --- |
| large_upload | retry0 failed 3/3; retry1 succeeded 3/3 after one failed first attempt | No single-session browser CM; one retry1 row had qlog path validation but Chrome used two sessions | Strongest user-task continuity case; upload failure maps directly to task failure |
| large_download | timeout-only retry0 failed 3/3; timeout+retry1 succeeded 3/3; local Range 6000ms no-retry 1/3 PASS and retry2 3/3 PASS | No single-session browser CM; Range retry rows used multiple Chrome QUIC sessions | Shows HTTP/3 alone did not preserve long response, while app recovery can be full-retry or resumable-range recovery |
| polling_dashboard | one valid no-retry public row failed after two poll requests; retry public rows invalid until page-ready runner | No qlog path validation in valid public failure row | Useful for dashboard/workflow freshness but requires page-ready public rerun |
| media_segments | segment replication 3000ms/6000ms completed 3/3; buffered playback 3000ms completed 12/12 but low buffer had 14 rebuffer events while high buffer had ~15s startup delay and 0 rebuffer | Not single-session CM; every buffered playback row classified nat_rebinding_multiple_quic_sessions | Shows streaming continuity can be preserved while hiding transport CM gaps, and must be measured with startup/rebuffer metrics |
| music_like_buffered | 6000ms no-retry failed 3/3 after first segment; retry1 completed 3/3 with all eight segments | Not single-session CM; retry1 rows used three Chrome QUIC sessions and no qlog path validation | Use as application-recovery control showing streaming continuity depends on retry/buffer policy |

## 스트리밍/대용량 Case 분해

| case | priority | network pattern | 다음 실험 | 해석 위험 |
| --- | --- | --- | --- | --- |
| Large upload | 1 | long-lived client-to-server body | Repeat page-ready public handover with retry0 and retry1 | Retry success can be reconnect/multiple-session recovery rather than QUIC CM |
| Large download | 2 | long-lived server-to-client body | Repeat page-ready public handover with timeout-only and retry-enabled download | Range or fetch retry can hide missing single-session migration |
| Live or low-latency video | 3 | small segments with tight timing and low buffer | Run media segments with short interval and page-ready handover after first segment | Segment retry may preserve playback semantics without proving QUIC CM |
| Video on demand | 4 | small segments with larger buffer | Run media segments with larger interval/buffer and compare no-retry vs retry | Buffering makes user-visible failure less likely even when transport migrates poorly |
| Music streaming | 5 | small low-bitrate segments with larger effective buffer | Use smaller bytes and longer interval as a low-sensitivity control | Audio may be too tolerant and should be framed as a low-sensitivity negative/control workload |

## 다음 실험 Matrix

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

## 가설

- H1: Chrome 브라우저에서 active Wi-Fi-to-iPhone-USB failover가 발생해도, 긴 downlink/upload는 application recovery 없이 안정적으로 single-session continuity를 보장하지 못할 가능성이 높다.
- H2: retry, Range resume, segment retry는 task completion을 올릴 수 있지만, Chrome target QUIC session churn과 completion latency를 함께 증가시킬 수 있다.
- H3: buffered media는 transport CM이 실패하거나 관찰되지 않아도 playback completion을 달성할 수 있다. 이때 논문 결과는 `CM 성공`이 아니라 startup delay/rebuffer/session churn의 QoE tradeoff로 써야 한다.
- H4: low-latency video는 VOD/music보다 CM 또는 application recovery의 효과가 더 잘 드러날 가능성이 높다. 그러나 현재 local result에서는 small/music-like segment도 no-retry에서 실패했으므로, bitrate만으로 민감도를 단정하면 안 된다.

## Evidence Ladder

| level | 의미 | 필수 증거 | 논문 표현 |
| --- | --- | --- | --- |
| L0 | HTTP/3 capability | Alt-Svc 또는 Chrome NetLog application H3 | H3 baseline |
| L1 | task continuity | DOM completion 또는 upload/download/media complete | 작업이 완료됐다 |
| L2 | path-change continuity | client path snapshot + server tuple/qlog 변화 | 경로 변화 중 작업 완료 |
| L3 | single-session browser CM | L2 + Chrome target QUIC session count 1 + qlog path validation | 브라우저 single-session CM evidence |
| L4 | workload/QoE impact | L3 또는 L2 + latency/rebuffer/retry/session churn | workload별 사용자 영향 |

## 실험별 판정 규칙

- upload/download row는 task completion, retry count, bytes received, completion latency, Chrome session count를 같이 보고한다.
- Range row는 전체 응답 재시도와 byte-range 재시도를 분리한다.
- media row는 completion만 보지 않고 startup delay, rebuffer event, fetched/played segment count, retry count를 필수 metric으로 둔다.
- third-party public site는 H3 discovery/control로만 사용한다. 서버 qlog와 tuple을 볼 수 없으면 CM success claim에는 쓰지 않는다.
- iPhone USB trigger는 `latent Wi-Fi-loss-to-iPhone-USB cellular failover`로 명명한다. simultaneous active multipath라고 쓰지 않는다.

## 왜 스트리밍만으로 시작하지 않는가

스트리밍은 실제 사용자 영향이 큰 workload지만, buffer와 segment retry가 transport failure를 쉽게 가린다. 따라서 스트리밍 결과만 먼저 보면 `재생 완료`와 `CM 성공`을 혼동하기 쉽다. 논문 설득력을 위해서는 upload/download로 transport continuity gap을 먼저 잡고, 그 다음 streaming에서 application recovery와 QoE tradeoff를 보여주는 순서가 더 강하다.

## Source Anchors

- RFC 9000: QUIC transport의 connection migration/path validation 기준. <https://datatracker.ietf.org/doc/html/rfc9000>
- RFC 9114: HTTP/3는 QUIC 위의 HTTP mapping이며 application recovery semantics 자체를 보장하지 않는다. <https://datatracker.ietf.org/doc/html/rfc9114>
- ACM CCR 2025 `An Analysis of QUIC Connection Migration in the Wild`: wild/deployment 관점의 CM 관측 경계 참고. <https://dl.acm.org/doi/10.1145/3727063.3727066>
- IETF Media over QUIC WG: media delivery가 QUIC 위에서 새롭게 논의되고 있으나, 본 연구의 browser HTTP/3 segment-fetch model과는 claim boundary를 분리한다. <https://datatracker.ietf.org/wg/moq/about/>

## 다음 실행

현재 즉시 필요한 외부 조건은 public origin 복구다. origin이 살아나면 `P0 -> P1 no-heartbeat -> P1 heartbeat -> P2 upload/range -> P3 buffered media -> P4 Safari/Android` 순서로 간다.

재생성 명령: `python3 tools/build_workload_prioritized_experiment_design.py`
