# Artifact Cleanup Dry-run Plan

Generated: `2026-06-25`

## Summary

| metric | value |
| --- | --- |
| target free GiB | `7.0` |
| candidate policy | `review-unreferenced` |
| current free | `6.9 GiB` |
| free space needed | `142.7 MiB` |
| selected candidates | `24/24` |
| reclaimable from selected | `66.8 MiB` |
| projected free after selected cleanup | `6.9 GiB` |
| target met by selected cleanup | `no` |
| remaining external cleanup gap | `75.9 MiB` |

## Selected Candidates

| path | size | files | directories | recommendation |
| --- | ---: | ---: | ---: | --- |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` | 219 | 62 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` | 200 | 67 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-heartbeat-smoke-20260624` | `4.5 MiB` | 204 | 70 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` | 201 | 67 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` | 199 | 67 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` | 171 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` | 173 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` | 169 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` | 169 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` | 166 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` | 172 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` | 166 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | 170 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | 22 | 10 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | 11 | 4 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | 11 | 4 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | 10 | 4 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044030Z` | `7.8 KiB` | 3 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044223Z` | `6.9 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041952Z` | `6.7 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041915Z` | `4.2 KiB` | 1 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | 1 | 6 | `review-unreferenced` |

## Note

Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.

`candidate_policy=review-unreferenced` excludes artifact directories referenced by tracked CSVs or planned final trial ids.

This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.
