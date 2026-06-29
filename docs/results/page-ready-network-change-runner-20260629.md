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

Earlier iPhone USB checks showed that this Mac+iPhone setup can behave as a latent failover environment:

- With Wi-Fi on, `en0` is the only active usable IPv4 path and `iPhone USB (en8)` is present but inactive.
- With Wi-Fi off, `en8` becomes active and default route moves to iPhone USB/cellular.
- `tools/check_iphone_usb_latent_failover.py --measure` observed `latent_iphone_usb_failover_observed` with `ready_at_ms=575`.

Therefore the next experiment should use `ALLOW_LATENT_SECONDARY_PATH=1`, `NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off"`, and should report the environment as delayed Wi-Fi-loss-to-iPhone-USB failover rather than simultaneous active-secondary-path migration.

Current rerun note: `docs/results/iphone-usb-current-detection-20260629.md` recorded `iphone_usb_not_detected`. Do not run the page-ready active public rows until macOS again exposes `iPhone USB (en8)` as a present network interface and `tools/check_iphone_usb_latent_failover.py --measure --restore-wifi` returns `latent_iphone_usb_failover_observed`.

## Next Experiment

Run a matched polling pair after the iPhone USB path is active:

1. No retry: `count=6`, `interval_ms=1000`, `retry_attempts=0`.
2. Retry: `count=6`, `interval_ms=1000`, `retry_attempts=2` or higher.

Both should use the page-ready trigger above. The result should distinguish:

- main-navigation failure,
- polling task failure,
- polling task recovery via application retry,
- observable single-session QUIC path migration.
