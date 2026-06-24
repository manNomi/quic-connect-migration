# Artifact Cleanup Dry-run Plan

Generated: `2026-06-24`

## Summary

| metric | value |
| --- | --- |
| target free GiB | `5.0` |
| current free | `1.6 GiB` |
| free space needed | `3.4 GiB` |
| selected candidates | `40/40` |
| reclaimable from selected | `908.3 MiB` |
| projected free after selected cleanup | `2.5 GiB` |
| target met by selected cleanup | `no` |
| remaining external cleanup gap | `2.5 GiB` |

## Selected Candidates

| path | size | files | directories |
| --- | ---: | ---: | ---: |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-localhost-20260624` | `383.5 MiB` | 249 | 95 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624` | `382.6 MiB` | 249 | 95 |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` | 219 | 62 |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-youtube-generate204-20260624` | `5.9 MiB` | 213 | 62 |
| `repro/quic-go-min-repro/artifacts/controlled-public-h3-browser-wrapper-google-smoke-20260624` | `5.7 MiB` | 212 | 63 |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-google-generate204-20260624` | `5.6 MiB` | 211 | 62 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-inactive-if-toggle` | `4.7 MiB` | 202 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-slow-inactive-if-toggle` | `4.7 MiB` | 202 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-nochange` | `4.7 MiB` | 200 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` | 200 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-ip-20260624` | `4.3 MiB` | 197 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-trace-20260624` | `4.3 MiB` | 186 | 55 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-local-20260624` | `4.3 MiB` | 195 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-ignore-cert-local-20260624` | `4.2 MiB` | 195 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-inactive-if-toggle-20260624` | `4.2 MiB` | 211 | 70 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-v2-20260624` | `4.2 MiB` | 199 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-grace-20260624` | `4.1 MiB` | 199 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` | 201 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` | 199 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-cdp-nochange-20260624` | `4.0 MiB` | 200 | 67 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-classifier-pass` | `4.0 MiB` | 168 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` | 171 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-vtime-pass` | `3.9 MiB` | 173 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` | 173 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` | 169 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` | 169 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` | 166 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` | 172 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` | 166 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | 170 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-20260624` | `3.6 MiB` | 168 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624-rerun` | `3.6 MiB` | 165 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | 22 | 10 |
| `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | 11 | 4 |
| `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | 11 | 4 |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | 10 | 4 |
| `repro/quic-go-min-repro/artifacts/controlled-public-preflight-20260624T094137Z` | `1.8 KiB` | 2 | 1 |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | 1 | 6 |

## Note

Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.

This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.
