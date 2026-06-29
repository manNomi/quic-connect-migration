# Controlled Public Range-Retry iPhone USB Handover

Generated: `2026-06-29`

This report is public-safe. It omits the concrete public origin hostname, public
IP addresses, SSH target, and local network addresses.

## Research Question

Can a large-download style HTTP/3 workload remain user-visible complete during
a Wi-Fi to iPhone USB path change when browser-level QUIC Connection Migration
is not observed?

This test intentionally separates two claims:

- Transport claim: whether the same QUIC connection migrates with path
  validation evidence.
- Application claim: whether a byte-range retry strategy completes the user's
  download task despite a path change.

## Setup

| field | value |
| --- | --- |
| client | `macOS Chrome` |
| secondary path | `iPhone USB` |
| origin | `fresh controlled public EC2 origin` |
| server | `quic-go HTTP/3 harness` |
| TLS | `WebPKI certificate on temporary sslip.io origin` |
| retry=2 baseline trial | `controlled-public-chrome-range-retry-nochange-fresh-20260629-001` |
| retry=2 active trials | `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` through `003` |
| retry=0 baseline trial | `controlled-public-chrome-range-noretry-nochange-fresh-20260629-001` |
| retry=0 active trials | `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001` through `002` |
| active trigger | after at least `131072` bytes completed |
| network change command | Wi-Fi disabled; wrapper restored Wi-Fi after the run |

Workload:

- Page: `GET /browser-range-download`
- Range transfer: repeated `GET /range-download`
- Total bytes: `524288`
- Range size: `131072`
- Retry budgets tested: `0` and `2`

## Result Summary

| condition | retry budget | runs | status | classification | qlog path validation | application result |
| --- | ---: | ---: | --- | --- | --- | --- |
| no-change baseline | 0 | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `false` | `1/1` completed |
| no-change baseline | 2 | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `false` | `1/1` completed |
| Wi-Fi to iPhone USB | 0 | 2 | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `false` in all runs | `0/2` completed |
| Wi-Fi to iPhone USB | 2 | 3 | `PASS_NEGATIVE_CONTROL` | mixed negative controls | `false` in all runs | `2/3` completed |

Active trial details:

- The client active path changed from Wi-Fi to iPhone USB in the successful
  active runs.
- The server observed two target H3 remote tuples in the successful active
  runs.
- Server qlog did not show QUIC path validation evidence in any active run.
- Successful retry=2 active runs recorded one transient
  `TypeError: Failed to fetch` and then completed the full `524288` byte task
  by retrying a byte range.
- The failed active runs reached only `262144` bytes and recorded terminal
  `rangeError`.
- Wi-Fi was restored after the wrapper completed.

## Retry=2 Active Repetitions

| trial | immediate client path | eventual client path | target H3 tuples | application success | completed bytes | retries | classification |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| `001` | `client_active_path_changed` | `no_client_path_change_observed` | 2 | `true` | 524288 | 1 | `tuple_changed_without_path_validation` |
| `002` | `interface_set_changed_without_route_change` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |
| `003` | `client_active_path_changed` | `client_active_path_changed` | 2 | `true` | 524288 | 1 | `tuple_changed_without_path_validation` |

## Retry=0 Active Repetitions

| trial | immediate client path | eventual client path | target H3 tuples | application success | completed bytes | retries | classification |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| `001` | `client_active_path_changed` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |
| `002` | `client_active_path_changed` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |

An additional local failover probe immediately before trial `003` observed
iPhone USB becoming the default path in roughly `675 ms` after Wi-Fi disable.
This supports the interpretation that the failed run was caused by variable
secondary-path activation timing rather than a permanently unavailable iPhone
USB path.

## Interpretation

This is not evidence of successful browser-level QUIC Connection Migration. The
classifier correctly treats it as a negative control because the tuple changed
without qlog path validation.

It is strong evidence for a different paper point: user-visible continuity is
workload-dependent, retry-budget-dependent, and timing-dependent. A byte-range
download can recover from a path-change interruption through application-level
retry/resume even when transport-level CM is not observed, but only if the
replacement path becomes usable before the retry budget and browser fetch
failure behavior terminate the task. With no retry budget, the same workload
completed under no-change conditions but repeatedly failed under active
handover. Therefore, the paper should avoid saying "HTTP/3 CM guarantees
download continuity" and instead separate:

1. QUIC path migration evidence,
2. replacement-session or tuple-change evidence, and
3. application recovery semantics such as retry, byte-range resume, buffering,
   or upload retry.

## Reproducibility Pointers

Validation artifacts:

- `docs/results/controlled-public-chrome-range-noretry-nochange-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002-validation.md`
- `docs/results/controlled-public-chrome-range-retry-nochange-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002-validation.md`
- `docs/results/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003-validation.md`

Raw artifacts are intentionally ignored by git:

- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-noretry-nochange-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-002`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-nochange-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-002`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-003`

Harness wrapper:

- `harness/scripts/run-aws-controlled-public-chrome-trial.sh`

## Next Replication Plan

Next compare against:

- full-response downlink without range resume,
- upload retry workloads, and
- media-segment workloads with and without retry/buffer.

The expected paper use is a workload taxonomy: transport CM maturity should be
reported separately from application-level work preservation.
