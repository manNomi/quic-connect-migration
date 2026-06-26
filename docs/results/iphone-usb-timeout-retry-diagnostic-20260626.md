# iPhone USB Timeout Retry Diagnostic (2026-06-26)

## Purpose

This diagnostic checks whether a browser-level HTTP/3 task can recover through an application-level stream timeout and retry when Chrome is moved from Wi-Fi (`en0`) to iPhone USB tethering (`en8`) during an in-flight downlink stream.

The key distinction is intentional:

- A QUIC Connection Migration result requires the same connection to validate and use a new path, with server qlog evidence such as `PATH_CHALLENGE` / `PATH_RESPONSE`.
- An application recovery result can still complete the user task by aborting a stuck fetch and retrying, even if Chrome opens a replacement QUIC connection instead of migrating the old one.

## Harness Changes

`repro/quic-go-min-repro/cmd/h3server/main.go` now accepts `stream_timeout_ms` on `/browser-downlink`.

When `stream_timeout_ms > 0`, the browser page wraps each `ReadableStreamDefaultReader.read()` call with a timeout. If no stream progress is observed before the timeout, the page aborts the fetch via `AbortController`, records `downlinkLastError`, and lets the existing `retry_attempts` loop start a new `/downlink-stream` request.

`tools/classify_controlled_public_h3_baseline.py` was also refined so `downlinkLastError` is treated as a retry diagnostic rather than a terminal application failure when `downlinkComplete=true`. Terminal errors such as `downlinkError` still mark the task as failed.

## Environment

- Client: macOS Chrome runner
- Initial path: Wi-Fi `en0`
- New path: iPhone USB tethering `en8`
- Origin: controlled public quic-go HTTP/3 server on EC2
- Hostname: `43-203-244-29.sslip.io`
- Workload: `/browser-downlink?duration_ms=8000&chunks=8&bytes=32768`
- Network-change trigger: `networksetup -setairportpower en0 off`
- Trigger timing: 2 seconds after starting the browser workload
- Retry policy: `retry_attempts=1`, `retry_delay_ms=500`

## Results

| Condition | Repetitions | Application success | Retry used | Target H3 tuple change | Chrome QUIC sessions | Server qlog path validation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `stream_timeout_ms=1500` | 3 | 3/3 | 3/3 | 2/3 | 2 in every row | 0/3 |
| `stream_timeout_ms=3000`, `retry_attempts=0` | 3 | 0/3 | 0/3 | 0/3 | 1 in every row | 0/3 |
| `stream_timeout_ms=3000` | 3 | 3/3 | 3/3 | 3/3 | 2 in every row | 0/3 |

The 1500ms condition verifies that the timeout/retry mechanism works, but its timeout can fire before the 2s network-change trigger. It is useful as a harness diagnostic, not as the strongest handover claim.

The 3000ms condition is the stronger result. The first retry error was recorded at 3029-4029ms, after the 2s Wi-Fi cutover trigger. With no retry, all three repetitions failed at 3026-3035ms after receiving only 4122 bytes. With one retry, all three repetitions completed the 8s/32KB downlink task.

## Interpretation

The timeout+retry strategy restored application-level task completion in the public Chrome iPhone USB handover setup. The timeout-only control did not: it only turned the stuck stream into an explicit application failure.

It did not demonstrate browser QUIC Connection Migration. In the 3000ms condition, every row had:

- `downlinkComplete=true`
- `downlinkRetriesUsed=1`
- `target_h3_remote_addr_count=2`
- Chrome target QUIC sessions = 2
- server qlog `path_challenge=0`
- server qlog `path_response=0`

That evidence points to replacement or multiple HTTP/3 connections after the fetch retry, not single-connection QUIC migration. This makes the result useful for the paper because it separates two claims:

1. Chrome did not provide observable single-session QUIC Connection Migration in this active Wi-Fi to iPhone USB test.
2. A small application-level timeout+retry policy can still preserve the user-visible downlink task under the same handover.

The timeout-only control sharpens the second claim. Under the same 2s active path change and 3000ms stream timeout, `retry_attempts=0` failed 3/3 with `downlinkError=Error: AbortError: BodyStreamBuffer was aborted`, while `retry_attempts=1` succeeded 3/3. This isolates retry/reconnect behavior as the recovery mechanism.

## Relation To Prior Controls

The same stable 8s/32KB iPhone USB no-change workload passed before active handover testing. The no-retry active handover controls failed or remained incomplete across repetitions and trigger timings. The heartbeat diagnostic showed that separate application requests can receive responses after cutover, but that alone did not recover the original streaming task.

This diagnostic closes that gap: explicit stream timeout plus retry recovered the task while still showing no qlog path validation.

## Data

- Detailed CSV: `data/iphone-usb-timeout-retry-diagnostic-20260626.csv`
- Main artifacts:
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry0-iphone-usb-network-change-001`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry0-iphone-usb-network-change-002`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry0-iphone-usb-network-change-003`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry1-iphone-usb-network-change-001`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry1-iphone-usb-network-change-002`
  - `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-boundary8000-32kb-timeout3000-retry1-iphone-usb-network-change-003`
