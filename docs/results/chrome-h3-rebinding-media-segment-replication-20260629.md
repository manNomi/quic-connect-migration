# Chrome H3 Rebinding Media Segment Replication

Generated: `2026-06-29`

## Scope

This report summarizes local Chrome forced-H3 media-segment workloads under UDP rebinding and transient server-to-client packet loss. These are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Grouped Result

| profile | drop window | retry | PASS/runs | media complete | median elapsed ms | Chrome sessions | classification | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| video-like-segments | 3000ms | 0 | 3/3 | 3/3 | 5476 | 2-2 | nat_rebinding_multiple_quic_sessions=3 | 0 |
| video-like-segments | 6000ms | 0 | 3/3 | 3/3 | 8895 | 2-3 | nat_rebinding_multiple_quic_sessions=3 | 2 |

## Run Detail

| profile | trial | drop | status | classification | complete | segments | elapsed ms | Chrome sessions | qlog C/R | dropped A/B | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| video-like-segments | chrome-h3-rebinding-media-rep1-drop3000-retry0-20260629 | 3000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 6391 | 2 | 6/4 | 58/5 | 0 |
| video-like-segments | chrome-h3-rebinding-media-rep2-drop3000-retry0-20260629 | 3000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 5423 | 2 | 7/4 | 55/6 | 0 |
| video-like-segments | chrome-h3-rebinding-media-rep3-drop3000-retry0-20260629 | 3000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 5476 | 2 | 7/4 | 55/6 | 0 |
| video-like-segments | chrome-h3-rebinding-media-rep1-drop6000-retry0-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 8895 | 3 | 7/3 | 71/7 | 1 |
| video-like-segments | chrome-h3-rebinding-media-rep2-drop6000-retry0-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 8941 | 3 | 6/3 | 72/6 | 1 |
| video-like-segments | chrome-h3-rebinding-media-rep3-drop6000-retry0-20260629 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 8877 | 2 | 7/4 | 68/6 | 0 |

## Interpretation Boundary

A media row with `PASS` and `media complete=true` is user-visible segment-task continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to compare workload sensitivity: segment-based media can preserve visible continuity through request granularity, duplicate segment fetches, or multiple QUIC sessions, while large upload/download workloads expose failure more directly.

## Data

- CSV: `data/chrome-h3-rebinding-media-segment-replication-20260629.csv`
