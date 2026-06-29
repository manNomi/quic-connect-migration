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
| media segments | live/low-latency video-like segment fetch | local UDP rebinding pilot + 3x replication | 3000ms and 6000ms replicated 3/3 PASS without explicit app retry | multiple sessions/replacement behavior, not single-session CM | medium |
| music-like buffered media | small low-bitrate buffered segments | local UDP rebinding retry control | 6000ms no-retry failed 3/3; retry1 completed 3/3 | application retry/reconnect, not single-session CM | medium/control |

## Main Interpretation

The strongest research target remains large upload and large download. They make failure visible at the user-task level and have clear success/failure criteria.

Streaming is still important, but not because it always proves QUIC CM. Segment-based video or music can survive disruption through request granularity, buffering, retry, and browser session churn. This means streaming can be used to show why CM adoption is hard to evaluate: user-visible continuity may be preserved even when single-session transport continuity is absent.

The media segment pilot and replication are the clearest examples. The original 500-6000ms local transient outage pilot completed with `MEDIA_RETRY_ATTEMPTS=0`, and the repeated 3000ms/6000ms runs also completed 3/3 each. Every replication row was classified as `nat_rebinding_multiple_quic_sessions`, so this is user-visible continuity, not browser single-session CM success.

The music-like control sharpened the finding. Smaller 8192-byte segments with a longer 1000ms interval were not automatically tolerant: at 6000ms return-path loss, no-retry failed 3/3 after the first segment. Adding one segment retry converted the same profile to 3/3 completion, but all retry rows used three Chrome QUIC sessions. This supports the argument that streaming continuity is governed by segment cadence, retry timing, buffering, and session churn, not by QUIC CM alone.

## Paper Framing

Recommended paper framing:

> HTTP/3 Connection Migration should not be evaluated only as a binary transport feature. Its practical value depends on the workload's failure semantics. Long-lived uploads and downloads expose transport disruption as task failure, while segment-based media and polling workloads can convert the same disruption into retry, reconnect, stale data, buffer depletion, or session churn.

This framing avoids overclaiming. It also answers why a good transport feature may appear underused: many web workloads already rely on application-layer recovery or segmented delivery, while browsers and managed infrastructure may not expose or preserve single-session migration end to end.

## Immediate Next Experiments

1. Public page-ready polling handover once iPhone USB has active IPv4.
2. Public page-ready media segment handover once iPhone USB has active IPv4.
3. Add Range/resume download variant to compare retry restart versus resumable recovery.
4. Add a larger buffer-depth media model if the paper needs a deeper streaming section.
5. Compare public iPhone USB media rows against these local proxy controls.

## Data

- CSV: `data/workload-sensitivity-synthesis-20260629.csv`
- Upload source: `docs/results/iphone-usb-upload-retry-pilot-20260626.md`
- Download source: `docs/results/iphone-usb-timeout-retry-diagnostic-20260626.md`
- Polling source: `docs/results/iphone-usb-polling-runner-diagnostic-20260626.md`
- Media pilot source: `docs/results/chrome-h3-rebinding-media-segment-pilot-20260629.md`
- Media replication source: `docs/results/chrome-h3-rebinding-media-segment-replication-20260629.md`
- Music-like control source: `docs/results/chrome-h3-rebinding-music-like-media-control-20260629.md`
