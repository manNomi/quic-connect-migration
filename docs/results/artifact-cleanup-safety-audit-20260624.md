# Artifact Cleanup Safety Audit

Generated: `2026-06-24`

## Summary

| metric | value |
| --- | --- |
| experiments CSV | `data/experiment-results.csv` |
| disk free | `49.4 GiB` |
| target free GiB | `5.0` |
| artifact roots total | `1.0 GiB` |
| cleanup candidates | `47` |
| CSV-referenced candidates | `26` |
| planned final-trial candidates | `0` |
| review-unreferenced candidates | `19` |
| review-unreferenced size | `62.3 MiB` |
| protected referenced/planned size | `957.6 MiB` |
| projected free if review-unreferenced removed | `49.5 GiB` |
| target met if review-unreferenced removed | `yes` |
| remaining gap then | `0 B` |

## Recommendations

| recommendation | meaning |
| --- | --- |
| `keep-referenced` | referenced by `data/experiment-results.csv`; keep unless archived and paper evidence is preserved |
| `keep-planned-final-trial` | matches a planned final browser handover trial id |
| `review-controlled-public` | controlled-public preparation output; inspect manually before cleanup |
| `review-unreferenced` | not referenced by current CSV/planned final ids; still review before deletion |

## Candidates

| recommendation | path | size | referenced trials | reason |
| --- | --- | ---: | --- | --- |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-localhost-20260624` | `383.5 MiB` | chrome-h3-alt-svc-localhost-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624` | `382.6 MiB` | chrome-h3-alt-svc-ip-literal-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-bing-home-20260624` | `40.2 MiB` | chrome-public-h3-bing-home-20260624 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-home-20260624` | `26.2 MiB` | chrome-public-h3-cloudflare-home-20260624 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-instagram-home-20260624` | `20.4 MiB` | chrome-public-h3-instagram-home-20260624 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-facebook-home-20260624` | `15.5 MiB` | chrome-public-h3-facebook-home-20260624 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-blog-20260624` | `13.0 MiB` | chrome-public-h3-cloudflare-blog-20260624 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-youtube-generate204-20260624` | `5.9 MiB` | chrome-public-h3-youtube-204-001 | artifact path is referenced by data/experiment-results.csv |
| `review-controlled-public` | `repro/quic-go-min-repro/artifacts/controlled-public-h3-browser-wrapper-google-smoke-20260624` | `5.7 MiB` | - | controlled-public artifact may be related to public-origin preflight or final-trial preparation |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-google-generate204-20260624` | `5.6 MiB` | chrome-public-h3-google-204-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-inactive-if-toggle` | `4.7 MiB` | chrome-h3-slow-wifi-ip-inactive-if-toggle-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-inactive-if-toggle` | `4.7 MiB` | chrome-h3-slow-inactive-if-toggle-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-wifi-ip-nochange` | `4.7 MiB` | chrome-h3-slow-wifi-ip-nochange-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-ip-20260624` | `4.3 MiB` | chrome-h3-alt-svc-html-mkcert-ip-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-trace-20260624` | `4.3 MiB` | chrome-public-h3-cloudflare-trace-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-local-20260624` | `4.3 MiB` | chrome-h3-alt-svc-html-ip-literal-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-ignore-cert-local-20260624` | `4.2 MiB` | chrome-h3-alt-svc-html-ignore-cert-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-inactive-if-toggle-20260624` | `4.2 MiB` | chrome-h3-downlink-heartbeat-cdp-inactive-toggle-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-v2-20260624` | `4.2 MiB` | chrome-h3-alt-svc-html-mkcert-localhost-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-grace-20260624` | `4.1 MiB` | chrome-h3-downlink-heartbeat-cdp-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-cdp-nochange-20260624` | `4.0 MiB` | chrome-h3-downlink-noheartbeat-cdp-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-classifier-pass` | `4.0 MiB` | chrome-h3-local-poll-nochange-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-vtime-pass` | `3.9 MiB` | chrome-h3-local-sequence-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-20260624` | `3.6 MiB` | chrome-h3-downlink-noheartbeat-001 | artifact path is referenced by data/experiment-results.csv |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624-rerun` | `3.6 MiB` | chrome-h3-downlink-heartbeat-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/local-h3-midflight-rerun-20260624` | `1.7 MiB` | quic-go-local-h3-midflight-upload-rerun-20260624-001, quic-go-local-h3-midflight-download-rerun-20260624-001 | artifact path is referenced by data/experiment-results.csv |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |
| `keep-referenced` | `repro/quic-go-min-repro/artifacts/local-h3-workload-rerun-20260624` | `150.4 KiB` | quic-go-local-h3-workload-rerun-20260624-001 | artifact path is referenced by data/experiment-results.csv |
| `review-controlled-public` | `repro/quic-go-min-repro/artifacts/controlled-public-preflight-20260624T094137Z` | `1.8 KiB` | - | controlled-public artifact may be related to public-origin preflight or final-trial preparation |
| `review-unreferenced` | `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | - | artifact path is not referenced by the experiment CSV or planned final-trial ids |

## Note

Non-destructive audit only. Treat every item as review-required unless the referenced CSV rows and paper tables are backed up elsewhere.
