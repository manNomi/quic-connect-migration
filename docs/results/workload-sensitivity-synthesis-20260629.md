# Workload Sensitivity Synthesis (2026-06-29)

## Purpose

This synthesis answers the current research-direction question: if QUIC Connection Migration is useful, which web workloads actually expose the need for it?

The current evidence says the answer is workload-dependent. Upload and long download expose task failure directly. Polling and media segment workloads can shift the problem into retry, reconnect, session churn, or buffering.

## Summary Table

| workload | representative task | current evidence | continuity result | CM interpretation | paper priority |
| --- | --- | --- | --- | --- | --- |
| large upload | photo/video/field-record upload | public Chrome iPhone USB handover | retry0 failed 3/3; retry1 succeeded 3/3 | application retry/reconnect, not single-session CM | highest |
| large download | long file/export download | public Chrome iPhone USB handover | timeout-only failed 3/3; timeout+retry succeeded 3/3 | application timeout/retry, not single-session CM | high |
| polling dashboard | repeated dashboard fetch | one valid public failure row plus local controls | public no-retry failed; retry public rows need page-ready rerun | incomplete public retry evidence | medium |
| media segments | live/low-latency video-like segment fetch | local UDP rebinding transient pilot | 500-6000ms windows completed without explicit app retry | multiple sessions/replacement behavior, not single-session CM | medium |
| music-like buffered media | small low-bitrate buffered segments | planned | expected tolerant | likely low sensitivity | low/control |

## Main Interpretation

The strongest research target remains large upload and large download. They make failure visible at the user-task level and have clear success/failure criteria.

Streaming is still important, but not because it always proves QUIC CM. Segment-based video or music can survive disruption through request granularity, buffering, retry, and browser session churn. This means streaming can be used to show why CM adoption is hard to evaluate: user-visible continuity may be preserved even when single-session transport continuity is absent.

The media segment pilot is the clearest example. All four local transient outage rows completed with `MEDIA_RETRY_ATTEMPTS=0`, but every row used multiple Chrome QUIC sessions. The `6000ms` row completed all eight segments, duplicated one segment request, and used three target QUIC sessions. This is continuity, but not browser CM success.

## Paper Framing

Recommended paper framing:

> HTTP/3 Connection Migration should not be evaluated only as a binary transport feature. Its practical value depends on the workload's failure semantics. Long-lived uploads and downloads expose transport disruption as task failure, while segment-based media and polling workloads can convert the same disruption into retry, reconnect, stale data, buffer depletion, or session churn.

This framing avoids overclaiming. It also answers why a good transport feature may appear underused: many web workloads already rely on application-layer recovery or segmented delivery, while browsers and managed infrastructure may not expose or preserve single-session migration end to end.

## Immediate Next Experiments

1. Public page-ready polling handover once iPhone USB has active IPv4.
2. Public page-ready media segment handover once iPhone USB has active IPv4.
3. Local replication of media at 3000ms and 6000ms with 3 repetitions.
4. Add Range/resume download variant to compare retry restart versus resumable recovery.
5. Add a music-like media profile with smaller segments and longer interval as a low-sensitivity control.

## Data

- CSV: `data/workload-sensitivity-synthesis-20260629.csv`
- Upload source: `docs/results/iphone-usb-upload-retry-pilot-20260626.md`
- Download source: `docs/results/iphone-usb-timeout-retry-diagnostic-20260626.md`
- Polling source: `docs/results/iphone-usb-polling-runner-diagnostic-20260626.md`
- Media source: `docs/results/chrome-h3-rebinding-media-segment-pilot-20260629.md`
