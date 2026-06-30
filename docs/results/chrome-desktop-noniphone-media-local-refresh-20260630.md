# Chrome Desktop Non-iPhone Media Local Refresh

Generated: `2026-06-30`

This summary records a fresh local Chrome forced-H3 media-segment run that does not require iPhone input. It is a local UDP rebinding control, not a public Wi-Fi/LTE handover result.

## Purpose

The P5 gap in `non-iphone-research-gap-plan-20260630.md` asks whether Chrome desktop simulation can strengthen the browser/runtime-policy side of the study without requiring iPhone handover. This run reuses the existing local rebinding proxy harness and checks whether a media-segment workload can complete while preserving single target-session evidence.

## Command

```bash
WORKLOAD=media \
RUN_ID=chrome-desktop-noniphone-media-drop3000-retry0-20260630 \
REBIND_AFTER=1s \
DROP_A_SERVER_AFTER_SWITCH=1 \
DROP_A_SERVER_AFTER_SWITCH_FOR=3000ms \
MEDIA_SEGMENTS=6 \
MEDIA_INTERVAL_MS=250 \
MEDIA_SEGMENT_BYTES=32768 \
MEDIA_SEGMENT_DURATION_MS=100 \
MEDIA_SEGMENT_CHUNKS=2 \
MEDIA_RETRY_ATTEMPTS=0 \
CHROME_HOLD_SECONDS=10 \
CHROME_TIMEOUT_SECONDS=25 \
TIMEOUT=35s \
repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh
```

## Fresh Result

| field | value |
| --- | --- |
| status | `PASS` |
| classification | `nat_rebinding_possible_session_continuity` |
| browser application complete | `true` |
| DOM elapsed | `1895ms` |
| server request count | `7` |
| server remote tuple count | `2` |
| Chrome target QUIC sessions | `1` |
| target HTTP/3 jobs | `7` |
| server qlog PATH_CHALLENGE/PATH_RESPONSE | `1/1` |
| Chrome NetLog target PATH_CHALLENGE/PATH_RESPONSE | `1/1` |
| proxy switched | `true` |
| proxy client packets A/B | `63/24` |

This row is stronger than the earlier media replication rows for session attribution because the target Chrome QUIC session count is `1`, not `2-3`. It still remains a local control: the client interface, public IP, and OS route did not perform a real Wi-Fi/cellular handover.

## Aggregate

| field | value |
| --- | --- |
| runs | `1` |
| status counts | `{'PASS': 1}` |
| heartbeat counts | `{'noheartbeat': 1}` |
| classification counts | `{'nat_rebinding_possible_session_continuity': 1}` |
| heartbeat/classification counts | `{'noheartbeat::nat_rebinding_possible_session_continuity': 1}` |
| packet rebinding observed counts | `{'true': 1}` |
| NetLog target path validation counts | `{'true': 1}` |

## Runs

| run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH_CHALLENGE/PATH_RESPONSE | NetLog target PATH C/R | proxy client packets A/B | packet rebind |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| chrome-desktop-noniphone-media-drop3000-retry0-20260630 | noheartbeat | PASS | `nat_rebinding_possible_session_continuity` | 2 | 1 | 1/1 | 1/1 | 63/24 | true |

## Interpretation Boundary

Use these rows as repeated local controls for session-attribution risk. They confirm client packets were forwarded through both proxy upstream sockets, and Chrome NetLog target-session path frames can be compared with server qlog path validation. Packet rebinding, server tuple/path-validation evidence, and browser session-continuity evidence must still be interpreted separately. These rows do not complete the final controlled-public browser handover protocol.

Paper-safe statement:

> A fresh local Chrome forced-H3 media control completed a six-segment workload across proxy-induced UDP rebinding with one target QUIC session, two server-observed remote tuples, and both qlog and NetLog path-validation evidence. This supports the use of local browser controls for artifact interpretation, but it does not prove public browser handover continuity.
