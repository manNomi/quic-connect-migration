# Artifact Cleanup Apply Report

Generated: `2026-06-25`

This report is public-safe. It never prints qlog, NetLog, pcap, keylog, credential, domain, or device contents.

## Summary

| field | value |
| --- | --- |
| mode | `dry-run` |
| executed | `no` |
| target free GiB | `7.0` |
| candidate policy | `review-unreferenced` |
| selected candidates | `24` |
| selected reclaimable | `66.8 MiB` |
| remaining gap before cleanup | `964.3 MiB` |
| disk free before | `6.0 GiB` |
| disk free after | `6.0 GiB` |
| deleted count | `0` |
| confirm required | `DELETE-REVIEW-UNREFERENCED` |
| confirm ok | `no` |

## Refusal Reasons

- none

## Candidate Actions

| action | ok | path | size | reason |
| --- | --- | --- | ---: | --- |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-heartbeat-smoke-20260624` | `4.5 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044030Z` | `7.8 KiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044223Z` | `6.9 KiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041952Z` | `6.7 KiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041915Z` | `4.2 KiB` | validated review-unreferenced directory |
| `would-delete` | `yes` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | validated review-unreferenced directory |

## Note

Default mode is dry-run. Execution is allowed only for validated review-unreferenced artifact directories with the exact confirmation token.
