# Artifact Cleanup Dry-run Plan

Generated: `2026-06-30`

## Summary

| metric | value |
| --- | --- |
| target free GiB | `30.0` |
| candidate policy | `review-unreferenced` |
| current free | `20.6 GiB` |
| free space needed | `9.4 GiB` |
| selected candidates | `92/92` |
| reclaimable from selected | `7.1 GiB` |
| projected free after selected cleanup | `27.7 GiB` |
| target met by selected cleanup | `no` |
| remaining external cleanup gap | `2.3 GiB` |

## Selected Candidates

| path | size | files | directories | recommendation |
| --- | ---: | ---: | ---: | --- |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry2-20260629` | `223.6 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry0-hold35-20260629` | `222.6 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry2-hold35-20260629` | `222.6 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep1-drop6000-retry0-20260629` | `220.9 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep2-drop6000-retry2-20260629` | `220.7 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry0-hold35-20260629` | `219.2 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry2-hold35-20260629` | `218.9 MiB` | 228 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry0-hold35-20260629` | `218.7 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep1-drop6000-retry2-20260629` | `218.6 MiB` | 228 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep3-drop6000-retry0-20260629` | `218.3 MiB` | 225 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry2-20260629` | `216.1 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep3-drop6000-retry2-20260629` | `215.4 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry2-hold35-20260629` | `215.2 MiB` | 228 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry0-hold35-20260629` | `214.6 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry0-hold35-20260629` | `213.7 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep1-drop6000-retry1-hold24-20260629` | `212.6 MiB` | 227 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry2-20260629` | `212.4 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry2-hold35-20260629` | `211.3 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry2-hold35-20260629` | `209.7 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep2-drop6000-retry1-hold24-20260629` | `207.6 MiB` | 227 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry0-hold35-20260629` | `204.0 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry2-20260629` | `194.8 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry2-hold35-20260629` | `188.2 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-rep2-drop6000-retry0-20260629` | `188.0 MiB` | 227 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep3-drop6000-retry1-hold24-20260629` | `187.3 MiB` | 227 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry2-20260629` | `186.9 MiB` | 226 | 96 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry2-20260629` | `157.0 MiB` | 223 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry0-20260629` | `149.7 MiB` | 223 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep1-drop6000-retry1-20260629` | `146.3 MiB` | 224 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry0-20260629` | `143.4 MiB` | 223 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry0-20260629` | `142.0 MiB` | 223 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry0-20260629` | `139.7 MiB` | 225 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep3-drop6000-retry1-20260629` | `136.6 MiB` | 224 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry0-20260629` | `135.7 MiB` | 223 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry0-20260629` | `112.1 MiB` | 222 | 93 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep2-drop6000-retry1-20260629` | `102.2 MiB` | 224 | 93 | `review-unreferenced` |
| `harness/results/impl-rerun-20260630T070249Z` | `37.2 MiB` | 100 | 13 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep1-drop3000-retry0-20260629` | `29.8 MiB` | 218 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep2-drop6000-retry0-20260629` | `28.2 MiB` | 218 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep1-drop6000-retry0-20260629` | `27.9 MiB` | 218 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep2-drop6000-retry0-20260629` | `27.3 MiB` | 219 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep1-drop6000-retry0-20260629` | `27.3 MiB` | 219 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop6000-retry0-20260629` | `26.8 MiB` | 219 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep2-drop3000-retry0-20260629` | `26.4 MiB` | 218 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep3-drop3000-retry0-20260629` | `25.6 MiB` | 218 | 87 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-rep3-drop6000-retry0-20260629` | `25.4 MiB` | 216 | 84 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-musiclike-rep3-drop6000-retry0-20260629` | `24.6 MiB` | 218 | 87 | `review-unreferenced` |
| `harness/results/lsquic-nat-rebinding-demo-20260630T102751Z` | `13.5 MiB` | 13 | 2 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop3000-retry0-20260629` | `10.0 MiB` | 206 | 71 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop1500-retry0-20260629` | `9.9 MiB` | 203 | 68 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-media-drop500-retry0-20260629` | `9.9 MiB` | 203 | 68 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-smoke-streamed-20260629` | `9.7 MiB` | 203 | 68 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-range-smoke-20260629` | `9.6 MiB` | 202 | 68 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-buffered-media-smoke-20260629` | `8.8 MiB` | 203 | 68 | `review-unreferenced` |
| `harness/results/lsquic-preferred-address-script-20260630T095000Z` | `4.1 MiB` | 10 | 3 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-media-segment-smoke-20260629` | `4.0 MiB` | 186 | 62 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression-2` | `3.6 MiB` | 170 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-noheartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-inactive-if-toggle-20260624` | `3.5 MiB` | 170 | 59 | `review-unreferenced` |
| `harness/results/nginx-quic-active-migration-20260630T105518Z` | `3.3 MiB` | 17 | 10 | `review-unreferenced` |
| `harness/results/nginx-quic-active-migration-20260630T104210Z` | `3.2 MiB` | 15 | 9 | `review-unreferenced` |
| `harness/results/nginx-quic-active-migration-20260630T104639Z` | `3.2 MiB` | 15 | 10 | `review-unreferenced` |
| `harness/results/lsquic-preferred-address-demo-20260630T094528Z` | `3.2 MiB` | 11 | 3 | `review-unreferenced` |
| `harness/results/lsquic-preferred-address-script-20260630T095500Z` | `3.2 MiB` | 10 | 3 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-midflight` | `1.8 MiB` | 22 | 10 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/local-20260624T045440Z` | `1.4 MiB` | 11 | 4 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-happy-named` | `1.4 MiB` | 11 | 4 | `review-unreferenced` |
| `harness/results/chapter3-local-quic-go-20260630` | `1.4 MiB` | 14 | 4 | `review-unreferenced` |
| `harness/results/chapter3-local-quic-go-rerun-20260630` | `1.3 MiB` | 14 | 4 | `review-unreferenced` |
| `harness/results/nginx-quic-runtime-smoke-20260630T104134Z` | `1.1 MiB` | 15 | 9 | `review-unreferenced` |
| `harness/results/nginx-quic-runtime-smoke-20260630T104101Z` | `1.0 MiB` | 14 | 10 | `review-unreferenced` |
| `harness/results/nginx-quic-runtime-smoke-20260630T103946Z` | `1.0 MiB` | 14 | 10 | `review-unreferenced` |
| `harness/results/nginx-quic-runtime-smoke-20260630T103826Z` | `1.0 MiB` | 9 | 5 | `review-unreferenced` |
| `harness/results/nginx-quic-runtime-smoke-debug-20260630T103906Z` | `1.0 MiB` | 9 | 5 | `review-unreferenced` |
| `harness/results/packages` | `368.0 KiB` | 16 | 0 | `review-unreferenced` |
| `harness/results/lsquic-app-baseline-20260630T094443Z` | `155.4 KiB` | 9 | 3 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/verify-local-h3-workload` | `154.9 KiB` | 10 | 4 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-p0-baseline-preflight-current-20260625` | `14.4 KiB` | 6 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-p0-baseline-preflight-current-20260625b` | `14.3 KiB` | 6 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044030Z` | `7.8 KiB` | 3 | 1 | `review-unreferenced` |
| `harness/results/active-trials-20260626` | `7.0 KiB` | 2 | 0 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T044223Z` | `6.9 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T052907Z` | `6.8 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T072436Z` | `6.7 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041952Z` | `6.7 KiB` | 2 | 1 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/final-handover-run-next-20260625T041915Z` | `4.2 KiB` | 1 | 1 | `review-unreferenced` |
| `harness/results/aws-origin-20260629` | `3.8 KiB` | 3 | 1 | `review-unreferenced` |
| `harness/results/aws-origin-20260629T101252Z` | `3.6 KiB` | 4 | 0 | `review-unreferenced` |
| `harness/results/openlitespeed-runtime-preflight-20260630T120037Z` | `2.9 KiB` | 2 | 0 | `review-unreferenced` |
| `harness/results/aws-origin-20260625` | `362 B` | 1 | 0 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-html-mkcert-localhost-20260624` | `141 B` | 1 | 6 | `review-unreferenced` |
| `repro/quic-go-min-repro/artifacts/dry-run-precutover` | `0 B` | 0 | 2 | `review-unreferenced` |

## Note

Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.

`candidate_policy=review-unreferenced` excludes artifact directories referenced by tracked CSVs or planned final trial ids.

This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.
