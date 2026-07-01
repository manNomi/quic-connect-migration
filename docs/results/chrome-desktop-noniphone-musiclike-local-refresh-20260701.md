# Chrome Desktop Non-iPhone Music-Like Local Refresh

Generated: `2026-06-30` UTC / `2026-07-01` KST

## Scope

This report summarizes a fresh local Chrome forced-H3 music-like segment workload under UDP rebinding and transient server-to-client packet loss. It reruns the lower-bitrate segment profile without iPhone input. These are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Purpose

The earlier music-like control showed that small/low-bitrate segments are not automatically tolerant: a 6000ms outage failed without retry and recovered with one retry via multiple Chrome QUIC sessions. This refresh checks whether that direction still holds in the current Chrome/local harness state.

## Grouped Result

| profile | drop window | retry | PASS/runs | media complete | median elapsed ms | Chrome sessions | classification | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| music-like-buffered-segments-fresh | 6000ms | 0 | 0/1 | 0/1 | - | 2-2 | browser_h3_request_failed=1 | 0 |
| music-like-buffered-segments-fresh | 6000ms | 1 | 1/1 | 1/1 | 16786 | 3-3 | nat_rebinding_multiple_quic_sessions=1 | 0 |

## Run Detail

| profile | trial | drop | status | classification | complete | segments | elapsed ms | Chrome sessions | qlog C/R | dropped A/B | duplicate segments |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| music-like-buffered-segments-fresh | chrome-desktop-noniphone-musiclike-drop6000-retry0-20260701 | 6000ms | FAIL | browser_h3_request_failed | - | 1/8 | - | 2 | 0/0 | 14/18 | 0 |
| music-like-buffered-segments-fresh | chrome-desktop-noniphone-musiclike-drop6000-retry1-20260701 | 6000ms | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 16786 | 3 | 0/0 | 14/30 | 0 |

## Interpretation Boundary

A media row with `PASS` and `media complete=true` is user-visible segment-task continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to compare workload sensitivity: segment-based media can preserve visible continuity through request granularity, duplicate segment fetches, or multiple QUIC sessions, while large upload/download workloads expose failure more directly.

## Data

- CSV: `data/chrome-desktop-noniphone-musiclike-local-refresh-20260701.csv`
