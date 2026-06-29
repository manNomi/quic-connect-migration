# Page-Ready Network-Change Runner (2026-06-29)

## Purpose

The previous polling handover attempts exposed a sequencing problem: the network-change timer started in parallel with Chrome navigation. For dashboard-style polling workloads, this could switch the path before the `/browser-poll` page reached the origin, turning the trial into a main-navigation failure instead of an active workload-continuity experiment.

This update adds an optional page-readiness gate to the Chrome controlled-public network-change runner.

## Implementation

`tools/run_chrome_cdp_navigation.js` now accepts:

- `--ready-expression`: JavaScript expression evaluated in the page context.
- `--ready-timeout-seconds`: maximum wait time for the expression.
- `--ready-poll-interval-ms`: polling interval.
- `--ready-output`: JSON signal file written atomically when the expression passes or times out.

`repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh` now accepts:

- `NETWORK_CHANGE_READY_EXPR`
- `NETWORK_CHANGE_READY_TIMEOUT_SECONDS`
- `NETWORK_CHANGE_READY_POLL_INTERVAL_MS`
- `NETWORK_CHANGE_READY_FILE`

When `NETWORK_CHANGE_READY_EXPR` is not set, the runner keeps the old behavior: sleep `NETWORK_CHANGE_AFTER_SECONDS`, then execute `NETWORK_CHANGE_CMD`.

When `NETWORK_CHANGE_READY_EXPR` is set, the network-change process waits for the CDP ready signal first. After the signal passes, it still waits `NETWORK_CHANGE_AFTER_SECONDS`, which now acts as an offset after page readiness. If readiness fails or times out, the runner writes `results/network-change.json` with `error=ready_signal_failed` and does not execute the path-change command.

## Polling Trigger

The intended polling trigger is:

```bash
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.pollCompletedCount || "0") >= 1'
```

This makes the handover occur only after the browser has loaded `/browser-poll` and completed at least one `/poll` fetch. It avoids invalid rows where Chrome ends on `chrome-error://chromewebdata/` before the workload starts.

## Verification

Completed local checks:

- `node --check tools/run_chrome_cdp_navigation.js`
- `bash -n repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh`
- CDP smoke test with a `data:` page and `ready.ok=true`
- CDP timeout smoke test with `ready.ok=false` and `exit=1`
- `go test ./cmd/h3server`

## Current Execution Gate

The active iPhone USB path was not available at the time of implementation verification:

- `scutil --nwi` showed only `en0`.
- `ifconfig en8` returned `interface en8 does not exist`.
- `networksetup -listnetworkserviceorder` still listed `iPhone USB (en8)`, but the interface was not active.

The next experiment should be run only after iPhone USB Personal Hotspot appears as an active IPv4 interface.

## Next Experiment

Run a matched polling pair after the iPhone USB path is active:

1. No retry: `count=6`, `interval_ms=1000`, `retry_attempts=0`.
2. Retry: `count=6`, `interval_ms=1000`, `retry_attempts=2` or higher.

Both should use the page-ready trigger above. The result should distinguish:

- main-navigation failure,
- polling task failure,
- polling task recovery via application retry,
- observable single-session QUIC path migration.
