# Chrome H3 Rebinding Buffered Media Control

Generated: `2026-06-30 UTC / 2026-07-01 KST`

## Scope

This report summarizes local Chrome forced-H3 buffered-media playback workloads under UDP rebinding and transient server-to-client packet loss. It models a player that prefetches segments into a bounded buffer and consumes them on a playback clock. These rows are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Grouped Result

| profile | drop | retry | startup/max buffer | PASS/runs | playback complete | median startup ms | median elapsed ms | rebuffer events | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chrome-desktop-noniphone-buffered-refresh | 6000ms | 0 | 1/1 | 1/1 | 1/1 | 23 | 14058 | 6-6 | 3-3 | nat_rebinding_multiple_quic_sessions=1 |
| chrome-desktop-noniphone-buffered-refresh | 6000ms | 0 | 4/6 | 1/1 | 1/1 | 22 | 9043 | 1-1 | 3-3 | nat_rebinding_multiple_quic_sessions=1 |

## Run Detail

| profile | trial | drop | retry | startup/max | status | classification | complete | played | startup ms | elapsed ms | rebuffer | Chrome sessions | qlog C/R | dropped A/B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chrome-desktop-noniphone-buffered-refresh | chrome-desktop-noniphone-buffered-low-drop6000-retry0-20260701 | 6000ms | 0 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 23 | 14058 | 6 | 3 | 6/3 | 53/6 |
| chrome-desktop-noniphone-buffered-refresh | chrome-desktop-noniphone-buffered-high-drop6000-retry0-20260701 | 6000ms | 0 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 22 | 9043 | 1 | 3 | 6/3 | 55/6 |

## Interpretation Boundary

A completed buffered-media row is playback-level continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to separate streaming user experience metrics from transport continuity: startup delay and rebuffer events can change even when all rows eventually complete.

## Data

- CSV: `data/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.csv`
