# iPhone USB Upload Retry Pilot And Replication (2026-06-26)

## Purpose

This experiment extends the public Chrome iPhone USB handover work from downlink streams to upload tasks. The target scenario is closer to photo, video, or field-record upload workflows.

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

## Short Pilot

| Condition | Trigger | Retry | App result | Upload bytes | Retry used | Target H3 tuple count | Chrome QUIC sessions | qlog path validation |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 8s/32KB | 2s | 0 | failed | 28672 generated, 0 received | 0 | 1 | 1 | 0 |
| 8s/32KB | 2s | 1 | succeeded | 32768 received | 0 | 1 | 1 | 0 |

The short retry1 row is not strong retry-recovery evidence because the page completed without using the retry path. It shows timing variability: depending on when the upload POST is established relative to the cutover, the task may complete without an application retry.

## Long Replication

The stronger condition is `16s/64KB`, trigger at 4s. This makes the network cutover occur while the upload stream is active.

| Condition | Repetitions | Application success | Retry used | Partial first-attempt bytes | Target H3 tuple count | Chrome QUIC sessions | qlog path validation |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| retry0 | 3 | 0/3 | 0/3 | 28672, 45056, 40960 | 1 in every row | 1 in every row | 0/3 |
| retry1 | 3 | 3/3 | 3/3 | 65536 final bytes in every row | 2 in every row | 2 in every row | 1/3 |

Retry0 failed in every repetition with `TypeError: Failed to fetch`. Retry1 succeeded in every repetition after one failed first attempt. The successful retry1 rows completed at 22994-23196ms and returned `uploadResponseBytes=65536`.

One retry1 repetition had server qlog `PATH_CHALLENGE=2` and `PATH_RESPONSE=2`, but Chrome also had two target QUIC sessions and the application used a second upload attempt. This is therefore classified as reconnect or multiple sessions, not single-session QUIC Connection Migration.

One retry0 repetition received an unsolicited public-origin HTTP/1.1 scan request for `/cgi-bin/../../../../../../../../../../bin/sh`. It did not affect target H3 tuple counts, application state, or qlog path validation and is recorded in the CSV notes.

## Interpretation

The upload replication supports the same separation seen in downlink:

1. Observable single-session browser QUIC Connection Migration was not demonstrated.
2. Application-level retry preserved the user-visible upload task in 3/3 repetitions under the matched long upload condition.
3. Without retry, the same long upload condition failed in 3/3 repetitions.

This is a useful paper result because upload is a naturally expected web-application task in field workflows. The evidence says that HTTP/3 alone did not make Chrome continue the original upload across Wi-Fi to iPhone USB handover, but application retry restored task completion with extra latency and replacement/multiple-session behavior.

## Data

- Detailed CSV: `data/iphone-usb-upload-retry-pilot-20260626.csv`
- Main repeated artifacts:
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry0-iphone-usb-network-change-pilot-001`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry0-iphone-usb-network-change-002`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry0-iphone-usb-network-change-003`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry1-iphone-usb-network-change-pilot-001`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry1-iphone-usb-network-change-002`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-upload-boundary16000-64kb-trigger4s-retry1-iphone-usb-network-change-003`
