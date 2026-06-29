# Chrome H3 Local Rebinding Media Segment Pilot (2026-06-29)

## Purpose

This pilot tests the newly added media-segment workload under local UDP rebinding with transient server-to-client return-path loss. It is a local control, not public Wi-Fi to cellular handover evidence.

The research question is whether streaming-like segment fetches behave more like long-lived upload/download tasks or more like application-level recovery workloads.

## Workload

Each run used:

- `WORKLOAD=media`
- `MEDIA_SEGMENTS=8`
- `MEDIA_INTERVAL_MS=250`
- `MEDIA_SEGMENT_BYTES=32768`
- `MEDIA_SEGMENT_DURATION_MS=100`
- `MEDIA_SEGMENT_CHUNKS=2`
- `MEDIA_RETRY_ATTEMPTS=0`
- `REBIND_AFTER=500ms`
- A+B server-to-client packets dropped for the configured window after proxy switch

This models a live/low-latency segment-fetch pattern without invoking a browser media decoder.

## Results

| trial | drop window | app retry | status | classification | media complete | segments | elapsed ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B |
| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `drop500-retry0` | 500ms | 0 | PASS | `nat_rebinding_multiple_quic_sessions` | true | 8/8 | 2841 | 9 | 2 | 4/3 | 37/2 |
| `drop1500-retry0` | 1500ms | 0 | PASS | `nat_rebinding_multiple_quic_sessions` | true | 8/8 | 4135 | 9 | 2 | 6/4 | 53/5 |
| `drop3000-retry0` | 3000ms | 0 | PASS | `nat_rebinding_multiple_quic_sessions` | true | 8/8 | 5692 | 9 | 2 | 6/4 | 57/5 |
| `drop6000-retry0` | 6000ms | 0 | PASS | `nat_rebinding_multiple_quic_sessions` | true | 8/8 | 8938 | 10 | 3 | 6/3 | 72/6 |

## Reproduction Command

Replace `DROP_MS` and `RUN_ID` for each row:

```bash
RUN_ID=RUN_ID \
ARTIFACT_DIR=artifacts/RUN_ID \
WORKLOAD=media \
MEDIA_SEGMENTS=8 \
MEDIA_INTERVAL_MS=250 \
MEDIA_SEGMENT_BYTES=32768 \
MEDIA_SEGMENT_DURATION_MS=100 \
MEDIA_SEGMENT_CHUNKS=2 \
MEDIA_RETRY_ATTEMPTS=0 \
MEDIA_RETRY_DELAY_MS=500 \
REBIND_AFTER=500ms \
DROP_A_SERVER_AFTER_SWITCH=1 \
DROP_B_SERVER_AFTER_SWITCH=1 \
DROP_A_SERVER_AFTER_SWITCH_FOR=DROP_MSms \
DROP_B_SERVER_AFTER_SWITCH_FOR=DROP_MSms \
TIMEOUT=40s \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_HOLD_SECONDS=12 \
ALLOW_CLASSIFIER_FAIL=1 \
./scripts/run-chrome-h3-rebinding-proxy.sh
```

## Interpretation

The media segment workload completed in all four pilot windows without explicit application retry. This is materially different from the upload and downlink long-body controls, where application task failure or explicit retry boundaries are easier to expose.

However, every media row is classified as `nat_rebinding_multiple_quic_sessions`. The result is therefore not single-session browser QUIC Connection Migration evidence. It is evidence that segment-style workloads can preserve user-visible task completion through replacement or multiple-session behavior.

The `6000ms` row is especially informative: the browser completed all eight segments, the server saw one duplicate segment-3 request, and Chrome used three target QUIC sessions. This supports the paper framing that media workloads can hide transport continuity gaps through request/session churn.

## Paper Claim Boundary

Safe claim:

> Segment-based media workloads may retain user-visible continuity across path disruption even when the observable browser behavior is reconnect or multiple QUIC sessions rather than single-session QUIC Connection Migration.

Do not claim:

> Chrome successfully performed single-session QUIC Connection Migration for media streaming.

The latter would require a single target QUIC session, a target tuple/path change, path validation evidence, and application completion in the same row.

## Next Experiments

1. Repeat the media segment pilot with 3 repetitions at 3000ms and 6000ms.
2. Add a lower-sensitivity music-like profile: smaller segment bytes and longer interval.
3. Run the same media page-ready public handover after iPhone USB is active.
4. Compare media rows against upload and downlink rows in a workload-sensitivity synthesis table.

## Data

- CSV: `data/chrome-h3-rebinding-media-segment-pilot-20260629.csv`
- Artifacts:
  - `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop500-retry0-20260629`
  - `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop1500-retry0-20260629`
  - `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop3000-retry0-20260629`
  - `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop6000-retry0-20260629`
