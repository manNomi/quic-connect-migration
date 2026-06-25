# Artifact Cleanup Execution Log

Generated: `2026-06-25`

This log records local ignored artifact cleanup performed to unblock the final browser handover disk gate. It is public-safe and lists only directory names, sizes, and the cleanup policy.

## Summary

| field | value |
| --- | --- |
| mode | `execute` |
| target free GiB | `7.0` |
| candidate policy | `review-unreferenced` |
| batches | `3` |
| deleted directories | `12` |
| reclaimable deleted | `51.3 MiB` |
| safety condition | `validated review-unreferenced artifact directories only` |
| final planner gap | `0 B` |
| final disk gate | `disk_ready=yes` |

## Deleted Directories

| batch | path | size |
| ---: | --- | ---: |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | `7.4 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-nochange-check` | `4.6 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-rebinding-heartbeat-smoke-20260624` | `4.5 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-fixed-20260624` | `4.1 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-cdp-nochange-20260624` | `4.0 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-pass` | `4.0 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-svg-pass` | `3.9 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-classifier-regression` | `3.9 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-controlled` | `3.8 MiB` |
| 1 | `repro/quic-go-min-repro/artifacts/chrome-h3-downlink-heartbeat-20260624` | `3.7 MiB` |
| 2 | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-check` | `3.7 MiB` |
| 3 | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-realtime-nochange-check` | `3.7 MiB` |

## Post-Condition

`tools/plan_artifact_cleanup.py --target-free-gib 7 --candidate-policy review-unreferenced` reported `free space needed=0 B` after the third batch, and `tools/check_next_final_handover_trial_readiness.py` reported `disk_ready=yes`.
