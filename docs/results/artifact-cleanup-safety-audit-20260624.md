# Artifact Cleanup Safety Audit

Generated: `2026-06-24`

## Summary

| metric | value |
| --- | --- |
| experiments CSV | `data/experiment-results.csv` |
| disk free | `42.0 GiB` |
| target free GiB | `5.0` |
| artifact roots total | `4.4 GiB` |
| extra artifact reference CSVs | `['data/chrome-h3-rebinding-repetition-summary-20260624.csv', 'data/chrome-h3-rebinding-upload-summary-20260624.csv', 'data/chrome-h3-rebinding-timing-sensitivity-20260624.csv', 'data/chrome-h3-rebinding-old-path-drop-20260624.csv', 'data/chrome-h3-rebinding-old-path-drop-stress-20260624.csv', 'data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv', 'data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv', 'data/quic-go-h3-midflight-repetition-summary-20260624.csv']` |
| cleanup candidates | `64` |
| CSV-referenced candidates | `42` |
| planned final-trial candidates | `0` |
| review-unreferenced candidates | `20` |
| review-unreferenced size | `66.8 MiB` |
| protected referenced/planned size | `4.3 GiB` |
| projected free if review-unreferenced removed | `42.1 GiB` |
| target met if review-unreferenced removed | `yes` |
| remaining gap then | `0 B` |

## Recommendations

| recommendation | meaning |
| --- | --- |
| `keep-referenced` | referenced by a tracked artifact CSV; keep unless archived and paper evidence is preserved |
| `keep-planned-final-trial` | matches a planned final browser handover trial id |
| `review-controlled-public` | controlled-public preparation output; inspect manually before cleanup |
| `review-unreferenced` | not referenced by current artifact CSVs or planned final ids; still review before deletion |

## Candidates

| recommendation | path | size | referenced trials | reason |
| --- | --- | ---: | --- | --- |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-transient-return-path-sweep-20260624` | `1.8 GiB` | chrome-h3-rebinding-transient-return-path-sweep-local-001, downlink-1m-drop-ab-250ms, upload-1m-drop-ab-250ms, downlink-1m-drop-ab-1500ms, upload-1m-drop-ab-1500ms, downlink-1m-drop-ab-3000ms, upload-1m-drop-ab-3000ms, downlink-1m-drop-ab-6000ms, upload-1m-drop-ab-6000ms, downlink-1m-drop-ab-9000ms, upload-1m-drop-ab-9000ms | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-stress-20260624` | `812.7 MiB` | chrome-h3-rebinding-old-path-drop-stress-local-001, downlink-1m-noheartbeat, downlink-1m-heartbeat, downlink-4m-noheartbeat, upload-1m, upload-4m | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-return-path-drop-controls-20260624` | `534.1 MiB` | chrome-h3-rebinding-return-path-drop-controls-local-001, downlink-1m-drop-b-only, upload-1m-drop-b-only, downlink-1m-drop-a-and-b, upload-1m-drop-a-and-b | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-localhost-20260624` | `383.5 MiB` | chrome-h3-alt-svc-localhost-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624` | `382.6 MiB` | chrome-h3-alt-svc-ip-literal-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-old-path-drop-repetition-20260624` | `49.1 MiB` | chrome-h3-rebinding-old-path-drop-local-001, noheartbeat-r1, noheartbeat-r2, noheartbeat-r3, heartbeat-r1, heartbeat-r2, heartbeat-r3 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-repetition-20260624` | `49.0 MiB` | noheartbeat-r1, noheartbeat-r2, noheartbeat-r3, heartbeat-r1, heartbeat-r2, heartbeat-r3 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-bing-home-20260624` | `40.2 MiB` | chrome-public-h3-bing-home-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-timing-early-20260624` | `32.7 MiB` | chrome-h3-rebinding-timing-sensitivity-local-001, noheartbeat-r1, noheartbeat-r2, heartbeat-r1, heartbeat-r2 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-timing-late-20260624` | `32.6 MiB` | noheartbeat-r1, noheartbeat-r2, heartbeat-r1, heartbeat-r2 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-home-20260624` | `26.2 MiB` | chrome-public-h3-cloudflare-home-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-upload-old-path-drop-repetition-20260624` | `25.9 MiB` | upload-r1, upload-r2, upload-r3 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-upload-repetition-20260624` | `25.9 MiB` | chrome-h3-rebinding-upload-local-001, upload-r1, upload-r2, upload-r3 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-instagram-home-20260624` | `20.4 MiB` | chrome-public-h3-instagram-home-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-upload-timing-late-20260624` | `17.2 MiB` | upload-r1, upload-r2 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-upload-timing-early-20260624` | `17.2 MiB` | upload-r1, upload-r2 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-facebook-home-20260624` | `15.5 MiB` | chrome-public-h3-facebook-home-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-blog-20260624` | `13.0 MiB` | chrome-public-h3-cloudflare-blog-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-drop-oldpath-upload-20260624` | `8.7 MiB` | chrome-h3-rebinding-drop-oldpath-upload-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-heartbeat-smoke2-20260624` | `8.2 MiB` | chrome-h3-rebinding-heartbeat-local-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-drop-oldpath-downlink-20260624` | `8.1 MiB` | chrome-h3-rebinding-drop-oldpath-downlink-20260624 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-noheartbeat-smoke-20260624` | `8.1 MiB` | chrome-h3-rebinding-noheartbeat-local-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-youtube-generate204-20260624` | `5.9 MiB` | chrome-public-h3-youtube-204-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-controlled-public` | `repro/quic-go-min-repro/artifacts/controlled-public-h3-browser-wrapper-google-smoke-20260624` | `5.7 MiB` | - | controlled-public artifact may be related to public-origin preflight or final-trial preparation |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-google-generate204-20260624` | `5.6 MiB` | chrome-public-h3-google-204-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/quic-go-h3-midflight-repetition-20260624` | `5.3 MiB` | r1, r2, r3 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-inactive-if-toggle` | `4.7 MiB` | chrome-h3-slow-wifi-ip-inactive-if-toggle-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-inactive-if-toggle` | `4.7 MiB` | chrome-h3-slow-inactive-if-toggle-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-nochange` | `4.7 MiB` | chrome-h3-slow-wifi-ip-nochange-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-heartbeat-smoke-20260624` | `4.5 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-ip-20260624` | `4.3 MiB` | chrome-h3-alt-svc-html-mkcert-ip-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-trace-20260624` | `4.3 MiB` | chrome-public-h3-cloudflare-trace-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-local-20260624` | `4.3 MiB` | chrome-h3-alt-svc-html-ip-literal-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-ignore-cert-local-20260624` | `4.2 MiB` | chrome-h3-alt-svc-html-ignore-cert-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-inactive-if-toggle-20260624` | `4.2 MiB` | chrome-h3-downlink-heartbeat-cdp-inactive-toggle-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-v2-20260624` | `4.2 MiB` | chrome-h3-alt-svc-html-mkcert-localhost-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-grace-20260624` | `4.1 MiB` | chrome-h3-downlink-heartbeat-cdp-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-cdp-nochange-20260624` | `4.0 MiB` | chrome-h3-downlink-noheartbeat-cdp-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-classifier-pass` | `4.0 MiB` | chrome-h3-local-poll-nochange-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-vtime-pass` | `3.9 MiB` | chrome-h3-local-sequence-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-20260624` | `3.6 MiB` | chrome-h3-downlink-noheartbeat-001 | artifact path is referenced by a tracked artifact reference CSV |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624-rerun` | `3.6 MiB` | chrome-h3-downlink-heartbeat-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/local-h3-midflight-rerun-20260624` | `1.7 MiB` | quic-go-local-h3-midflight-upload-rerun-20260624-001, quic-go-local-h3-midflight-download-rerun-20260624-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/local-h3-workload-rerun-20260624` | `150.4 KiB` | quic-go-local-h3-workload-rerun-20260624-001 | artifact path is referenced by a tracked artifact reference CSV |
| `review-controlled-public` | `repro/quic-go-min-repro/artifacts/controlled-public-preflight-20260624T094137Z` | `1.8 KiB` | - | controlled-public artifact may be related to public-origin preflight or final-trial preparation |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | - | artifact path is not referenced by tracked artifact CSVs or planned final-trial ids |

## Note

Non-destructive audit only. Treat every item as review-required unless the referenced CSV rows and paper tables are backed up elsewhere.
