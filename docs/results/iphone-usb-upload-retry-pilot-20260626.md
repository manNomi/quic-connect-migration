# iPhone USB Upload Retry Pilot (2026-06-26)

## Purpose

This pilot extends the public Chrome iPhone USB handover work from downlink streams to upload tasks. The target scenario is closer to photo, video, or field-record upload workflows.

The question is not whether Chrome proves browser QUIC Connection Migration. The question is whether an upload task can be preserved by application-level retry when active Wi-Fi to iPhone USB path change interrupts the first upload attempt.

## Environment

- Client: macOS Chrome runner
- Initial path: Wi-Fi `en0`
- New path: iPhone USB tethering `en8`
- Origin: controlled public quic-go HTTP/3 server on EC2
- Hostname: `43-203-244-29.sslip.io`
- Workload: `/browser-upload`
- Network-change trigger: `networksetup -setairportpower en0 off`
- Evidence used: CDP body dataset, Chrome NetLog, server request log, server qlog

## Pilot Results

| Condition | Trigger | Retry | App result | Upload bytes | Retry used | Target H3 tuple count | Chrome QUIC sessions | qlog path validation |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 8s/32KB | 2s | 0 | failed | 28672 generated, 0 received | 0 | 1 | 1 | 0 |
| 8s/32KB | 2s | 1 | succeeded | 32768 received | 0 | 1 | 1 | 0 |
| 16s/64KB | 4s | 0 | failed | 28672 generated, 0 received | 0 | 1 | 1 | 0 |
| 16s/64KB | 4s | 1 | succeeded | 65536 received | 1 | 2 | 2 | 0 |

The short retry1 row is not strong retry-recovery evidence because the page completed without using the retry path. It shows timing variability: depending on when the upload POST is established relative to the cutover, the task may complete on the new path without an application retry.

The stronger matched pair is the 16s/64KB trigger4s condition:

- `retry_attempts=0`: failed at 5160ms with `uploadError=Error: TypeError: Failed to fetch`; server received the upload-sink request with 0 bytes.
- `retry_attempts=1`: first attempt failed at 7490ms with `TypeError: Failed to fetch`; second attempt completed 65536 bytes at 23196ms with `uploadRetriesUsed=1`.

## Interpretation

The long upload pilot supports the same separation seen in downlink:

1. Observable browser QUIC Connection Migration was not demonstrated. Server qlog had `PATH_CHALLENGE=0` and `PATH_RESPONSE=0`.
2. Application-level retry can recover a user-visible upload task, but the recovery appears to use a replacement or additional HTTP/3 session rather than single-session QUIC migration.

This is pilot evidence, not yet a full repetition set. It is strong enough to justify a follow-up replication sweep with at least 3 repetitions for the matched 16s/64KB trigger4s retry0/retry1 pair.

## Data

- Detailed CSV: `data/iphone-usb-upload-retry-pilot-20260626.csv`
- Main matched artifacts:
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry0-iphone-usb-network-change-pilot-001`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry1-iphone-usb-network-change-pilot-001`
