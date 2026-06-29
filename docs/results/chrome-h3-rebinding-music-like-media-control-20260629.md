# Chrome H3 Rebinding Media Segment Replication

Generated: `2026-06-29`

## Scope

This report summarizes local Chrome forced-H3 media-segment workloads under UDP rebinding and transient server-to-client packet loss. These are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Grouped Result

| profile | drop window | retry | PASS/runs | media complete | median elapsed ms | Chrome sessions | classification | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| music-like-buffered-segments | 6000ms | 0 | 0/3 | 0/3 | - | 2-2 | browser_h3_request_failed=3 | 0 |
| music-like-buffered-segments | 6000ms | 1 | 3/3 | 3/3 | 14076 | 3-3 | nat_rebinding_multiple_quic_sessions=3 | 0 |

## Run Detail

| profile | trial | drop | status | classification | complete | segments | elapsed ms | Chrome sessions | qlog C/R | dropped A/B | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep1-drop6000-retry0-20260629 | 6000ms | FAIL | browser_h3_request_failed | - | 1/8 | - | 2 | 0/0 | 13/18 | 0 |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep2-drop6000-retry0-20260629 | 6000ms | FAIL | browser_h3_request_failed | - | 1/8 | - | 2 | 0/0 | 14/18 | 0 |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep3-drop6000-retry0-20260629 | 6000ms | FAIL | browser_h3_request_failed | - | 1/8 | - | 2 | 0/0 | 14/18 | 0 |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep1-drop6000-retry1-hold24-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 14093 | 3 | 0/0 | 14/28 | 0 |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep2-drop6000-retry1-hold24-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 14073 | 3 | 0/0 | 11/28 | 0 |
| music-like-buffered-segments | chrome-h3-rebinding-musiclike-rep3-drop6000-retry1-hold24-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 14076 | 3 | 0/0 | 11/28 | 0 |

## Interpretation Boundary

A media row with `PASS` and `media complete=true` is user-visible segment-task continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to compare workload sensitivity: segment-based media can preserve visible continuity through request granularity, duplicate segment fetches, or multiple QUIC sessions, while large upload/download workloads expose failure more directly.

## Data

- CSV: `data/chrome-h3-rebinding-music-like-media-control-20260629.csv`
