# Final P0 Baseline Preflight Redaction Smoke

Generated: `2026-06-25`

This public-safe smoke run verifies that the final P0 baseline preflight wrapper fails closed and emits redacted operator artifacts when the ignored controlled-public origin config still contains placeholder values.

## Summary

| field | value |
| --- | --- |
| run id | `final-p0-baseline-preflight-redaction-smoke-20260625T080639Z` |
| wrapper | `harness/scripts/final-p0-baseline-preflight.sh` |
| exit | `1` |
| expected exit | `1` |
| result | `blocked as expected` |
| artifact size | `24 KiB` |
| artifact root | `repro/quic-go-min-repro/artifacts/final-p0-baseline-preflight-redaction-smoke-20260625T080639Z` |
| tracked raw artifacts | `no` |

## Command

```bash
RUN_ID=final-p0-baseline-preflight-redaction-smoke-20260625T080639Z CHECK_PUBLIC_ORIGIN=0 CHECK_LOCAL_FILES=0 bash harness/scripts/final-p0-baseline-preflight.sh
```

## Step Results

| step | result |
| --- | --- |
| `controlled_public_config` | `blocked(exit=1)` |
| `next_trial_selection` | `ok` |
| `next_trial_readiness` | `blocked(exit=1)` |
| `operator_checklist` | `ok` |
| `p0_baseline_preflight_guard` | `blocked(exit=1)` |

## Redaction Checks

The generated `final-handover-next-trial.md` and `final-handover-next-trial-readiness.md` both reported:

- `config source`: `local config (redacted)`
- `public-safe default`: `yes`
- `sensitive values redacted`: `yes`

The generated server/client command blocks used placeholders such as:

- `<redacted-public-origin-host>`
- `<redacted-tls-cert-file>`
- `<redacted-tls-key-file>`
- `<redacted-public-origin-url>`

The smoke artifact directory was scanned for private-domain, private-path, command-body, AWS-key, and private-key marker patterns. No matches were found.

## Interpretation

- This smoke does not run a browser H3 baseline and does not count toward the final browser handover protocol.
- It validates the operator wrapper safety behavior before real public-origin credentials are inserted locally.
- The next publishable experiment remains blocked on real public WebPKI origin host, URL, and TLS certificate/key paths.
