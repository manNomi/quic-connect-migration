# Non-iPhone Workload Continuity and QoE Synthesis

Generated: `2026-06-30 UTC / 2026-07-01 KST`

This public-safe synthesis normalizes the committed local Chrome/quic-go workload CSVs that do not require iPhone input. It compares video-like segment fetches, music-like segment fetches, buffered video playback, byte-range download, and upload controls under local UDP rebinding or local return-path loss.

## Summary

| field | value |
| --- | --- |
| source CSV count | `8` |
| normalized rows | `32` |
| workload groups | `5` |

## Workload Comparison

| workload | rows | PASS | complete | retry profile | drop ms | Chrome sessions | single-session rows | multi-session rows | path validation rows | QoE signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| buffered video playback | 14 | 14 | 14/14 | 0:8, 2:6 | 3000, 6000 | 2-3 | 0 | 14 | 13 | rebuffer 1-14; startup median 89ms |
| large byte-range download | 2 | 2 | 2/2 | 0:2 | 3000 | 1-1 | 2 | 0 | 2 | elapsed median 3608ms |
| large upload | 1 | 1 | 1/1 | 0:1 | 3000 | 1-1 | 1 | 0 | 1 | upload bytes 131072-131072; request tuples 1-1 |
| music-like segment | 8 | 4 | 4/8 | 0:4, 1:4 | 6000 | 2-3 | 0 | 8 | 0 | elapsed median 14084ms |
| video-like segment | 7 | 7 | 7/7 | 0:7 | 3000, 6000 | 1-3 | 1 | 6 | 7 | elapsed median 7634ms |

## Paper Use

| workload | paper use | claim boundary |
| --- | --- | --- |
| buffered video playback | Use for QoE framing: playback completion can hide rebuffer cost and session churn. | Do not claim public Wi-Fi/LTE handover or general browser CM deployment success. Do not claim zero-impact video continuity. |
| large byte-range download | Use as the strongest local resumable-download control with single target-session path evidence. | Do not claim public Wi-Fi/LTE handover or general browser CM deployment success. |
| large upload | Use as client-sending workload evidence and as a warning that request-level tuple logs can miss packet rebinding. | Do not claim public Wi-Fi/LTE handover or general browser CM deployment success. Do not use request tuple count alone as packet-level path evidence. |
| music-like segment | Use as a retry/reconnect boundary: low-bitrate segment traffic still failed without retry under 6000ms loss. | Do not claim public Wi-Fi/LTE handover or general browser CM deployment success. Do not call retry/reconnect recovery single-session CM. |
| video-like segment | Use as local segment-continuity evidence; separate single-session local rows from multiple-session recovery. | Do not claim public Wi-Fi/LTE handover or general browser CM deployment success. |

## Interpretation

1. The strongest local non-iPhone browser evidence is not one uniform result: range and upload rows show cleaner single-session/path-validation signals than buffered or music-like rows.
2. Streaming workloads must be reported with QoE and recovery mechanism fields, not only completion.
3. Multiple Chrome target QUIC sessions convert many successful user-visible rows into application recovery or replacement-session evidence, not single-session browser Connection Migration evidence.

## Next Public Trials

1. Recover or create an H3-ready public origin with Alt-Svc.
2. Run public range-download and upload page-ready trials first because local controls already define crisp completion/path-validation gates.
3. Run public buffered-media and music-like trials after that, reporting startup delay, rebuffer events, retry count, and Chrome session count together.

## Data

- CSV: `data/noniphone-workload-qoe-continuity-synthesis-20260701.csv`
