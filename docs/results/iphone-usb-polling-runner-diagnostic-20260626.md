# iPhone USB Polling Runner Diagnostic (2026-06-26)

## Purpose

This diagnostic starts the dashboard/polling branch of the public Chrome iPhone USB handover study.

Polling is different from upload and downlink. It is a repeated-fetch dashboard workload, so it can naturally recover only if later fetches can proceed after a path change. The first step was to add per-fetch retry support to `/browser-poll` and then test whether retry could recover the polling loop.

## Harness Change

`/browser-poll` now accepts:

- `retry_attempts`
- `retry_delay_ms`

Each `/poll` fetch is wrapped in a per-request retry loop. The browser records:

- `pollCompletedCount`
- `pollRetriesUsed`
- `pollLastError`
- `pollLastErrorElapsedMs`
- `pollElapsedMs`
- `pollComplete`
- `pollError`
- `pollErrorElapsedMs`

The classifier now recognizes `pollComplete=true` as application success and `pollError` as application failure.

## Valid No-Retry Result

The valid public iPhone USB polling row so far is:

- Condition: `count=6`, `interval_ms=1000`, trigger at 2s, `retry_attempts=0`
- Result: `PASS_NEGATIVE_CONTROL`
- Classification: `application_task_failed_without_quic_path_validation`
- Application: `pollError=TypeError: Failed to fetch`
- Server: main page loaded and two `/poll` H3 requests reached the server
- qlog: `PATH_CHALLENGE=0`, `PATH_RESPONSE=0`

This shows that a dashboard-like polling loop can fail under the same active Wi-Fi to iPhone USB handover where upload/downlink application retry can recover.

## Retry Precondition Problem

Three retry-enabled polling attempts were not valid workload results:

- `count=6`, trigger 2s, `retry_attempts=2`
- `count=6`, trigger 4s, `retry_attempts=2`
- `count=20`, trigger 10s, `retry_attempts=2`

In all three rows, the main `/browser-poll` page did not reach the server. Chrome ended on `chrome-error://chromewebdata/` with `ERR_CONNECTION_REFUSED`, while the server later timed out waiting for expected requests.

This means the current active-runner sequencing is not good enough for retry-enabled polling. The network-change timer starts in parallel with Chrome navigation, not after the polling page has loaded. If the timer fires before the HTTP/1.1 main page navigation reaches the controlled origin, the trial becomes a main-navigation failure rather than a polling continuity experiment.

## Interpretation

The polling branch is not complete yet.

What we can safely claim now:

1. The no-retry polling workload produced one valid active-handover failure row.
2. Polling retry instrumentation is implemented and tested locally.
3. Retry-enabled polling requires a runner that triggers network change after page/workload readiness, not merely after a fixed wall-clock delay from Chrome launch.

What we should not claim yet:

- That polling retry succeeds or fails under public iPhone USB handover.
- That dashboard continuity has been replicated in the controlled public setup.

## Next Step

Build a CDP runner mode that waits for a page readiness signal before executing the network-change command. For polling, a suitable trigger point is:

- `document.body.dataset.pollCompletedCount >= "1"` for active mid-loop handover, or
- a generic user-provided JavaScript predicate such as `document.body.dataset.pollCompletedCount`.

Update: the page-ready runner was implemented and smoke-tested in `docs/results/page-ready-network-change-runner-20260629.md`. The remaining gate is an active iPhone USB IPv4 interface for the public handover run.

Then rerun:

- no-retry polling: `count=6`, `interval_ms=1000`, trigger after first poll completion
- retry polling: same condition with `retry_attempts=2`

## Data

- Detailed CSV: `data/iphone-usb-polling-runner-diagnostic-20260626.csv`
- Main valid artifact: `repro/quic-go-min-repro/artifacts/controlled-public-chrome-poll-count6-interval1000-trigger2s-iphone-usb-network-change-001`
