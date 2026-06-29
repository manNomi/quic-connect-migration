# Controlled Public Full-Response Downlink iPhone USB Handover

Generated: `2026-06-29`

This report is public-safe. It omits the concrete public origin hostname, public
IP addresses, SSH target, and local network addresses.

## Research Question

How does a full-response HTTP/3 downlink workload behave during a Wi-Fi to
iPhone USB path change when browser-level QUIC Connection Migration is not
observed?

This is the comparison workload for the byte-range download experiments. The
purpose is to separate:

- a single long response that must survive as one browser fetch/read stream,
  from
- a resumable byte-range workload that can retry a failed chunk.

## Setup

| field | value |
| --- | --- |
| client | `macOS Chrome` |
| secondary path | `iPhone USB` |
| origin | `fresh controlled public EC2 origin` |
| server | `quic-go HTTP/3 harness` |
| TLS | `WebPKI certificate on temporary sslip.io origin` |
| baseline trial | `controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` |
| active trials | `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001` through `002` |
| active trigger | after any `downlinkBytes` were observed |
| network change command | Wi-Fi disabled; wrapper restored Wi-Fi after the run |

Workload:

- Page: `GET /browser-downlink`
- Stream: `GET /downlink-stream`
- Stream duration: `15000 ms`
- Chunks: `15`
- Downlink retry budget: `0`

## Result Summary

| condition | runs | status | classification | client path change | target H3 tuples | qlog path validation | application result |
| --- | ---: | --- | --- | --- | ---: | --- | --- |
| no-change baseline | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `n/a` | `n/a` | `false` | `1/1` completed |
| Wi-Fi to iPhone USB | 2 | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `client_active_path_changed` in both runs | `1` in both runs | `false` in both runs | `0/2` completed |

Active trial details:

| trial | client path | target H3 tuples | application success | bytes before error | terminal error | classification |
| --- | --- | ---: | --- | ---: | --- | --- |
| `001` | `client_active_path_changed` | 1 | `false` | 17528 | `downlinkError` | `application_task_failed_without_quic_path_validation` |
| `002` | `client_active_path_changed` | 1 | `false` | 17528 | `downlinkError` | `application_task_failed_without_quic_path_validation` |

Both active runs observed a real client path change from Wi-Fi to iPhone USB.
Neither run produced qlog path validation evidence. Neither run completed the
application task.

## Comparison With Byte-Range Download

| workload | retry budget | active runs | completed active runs | typical failure/completion signal | CM evidence |
| --- | ---: | ---: | ---: | --- | --- |
| full-response downlink | 0 | 2 | 0 | `downlinkError` after `17528` bytes | no qlog path validation |
| byte-range download | 0 | 2 | 0 | `rangeError` after `262144` bytes | no qlog path validation |
| byte-range download | 2 | 3 | 2 | `rangeComplete=true` after one retry in successful runs | no qlog path validation |

This comparison is the strongest current evidence for the application-layer
part of the paper. Under the same controlled public origin and same iPhone USB
handover mechanism, user-visible completion changed with workload semantics and
retry budget even though browser-level QUIC CM evidence remained absent.

## Interpretation

The full-response downlink trials reinforce a negative transport claim and a
positive application-semantics claim:

- Negative transport claim: these Chrome active handover rows must not be
  reported as successful browser QUIC Connection Migration, because qlog path
  validation was not observed.
- Application-semantics claim: preserving a web task during path change depends
  on how the workload can recover. A single fetch/read stream failed repeatedly,
  while a byte-range workload with retry completed in two of three active runs.

For the manuscript, this supports a workload taxonomy rather than a binary
"HTTP/3 CM works/does not work" claim.

## Reproducibility Pointers

Validation artifacts:

- `docs/results/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001-validation.md`
- `docs/results/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002-validation.md`

Related range report:

- `docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md`

Raw artifacts are intentionally ignored by git:

- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001`
- `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-002`

## Next Step

The next workload should be upload retry, because upload is another
user-visible task where application retry can change completion semantics but
does not imply single-session QUIC migration.
