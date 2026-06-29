# Chrome H3 Rebinding Buffered Media Control

Generated: `2026-06-29`

## Scope

This report summarizes local Chrome forced-H3 buffered-media playback workloads under UDP rebinding and transient server-to-client packet loss. It models a player that prefetches segments into a bounded buffer and consumes them on a playback clock. These rows are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Grouped Result

| profile | drop | retry | startup/max buffer | PASS/runs | playback complete | median startup ms | median elapsed ms | rebuffer events | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| buffered-media-playback | 3000ms | 0 | 1/1 | 3/3 | 3/3 | 67 | 22128 | 14-14 | 2-2 | nat_rebinding_multiple_quic_sessions=3 |
| buffered-media-playback | 3000ms | 0 | 4/6 | 3/3 | 3/3 | 15191 | 23215 | 0-0 | 2-2 | nat_rebinding_multiple_quic_sessions=3 |
| buffered-media-playback | 3000ms | 2 | 1/1 | 3/3 | 3/3 | 66 | 12100 | 3-14 | 2-2 | nat_rebinding_multiple_quic_sessions=3 |
| buffered-media-playback | 3000ms | 2 | 4/6 | 3/3 | 3/3 | 15177 | 23189 | 0-0 | 2-2 | nat_rebinding_multiple_quic_sessions=3 |

## Run Detail

| profile | trial | drop | retry | startup/max | status | classification | complete | played | startup ms | elapsed ms | rebuffer | Chrome sessions | qlog C/R | dropped A/B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 65 | 22128 | 14 | 2 | 3/2 | 14/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 112 | 22181 | 14 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 67 | 22114 | 14 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15244 | 23265 | 0 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15185 | 23206 | 0 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry0-hold35-20260629 | 3000ms | 0 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15191 | 23215 | 0 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep1-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 66 | 11096 | 3 | 2 | 6/4 | 40/5 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep2-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 67 | 12100 | 4 | 2 | 0/0 | 0/17 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-low-rep3-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 1/1 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 63 | 22100 | 14 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep1-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15177 | 23189 | 0 | 2 | 3/2 | 14/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep2-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15178 | 23191 | 0 | 2 | 3/2 | 0/1 |
| buffered-media-playback | chrome-h3-rebinding-buffered-media-high-rep3-drop3000-retry2-hold35-20260629 | 3000ms | 2 | 4/6 | PASS | nat_rebinding_multiple_quic_sessions | true | 8/8 | 15165 | 23182 | 0 | 2 | 3/2 | 0/1 |

## Interpretation Boundary

A completed buffered-media row is playback-level continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to separate streaming user experience metrics from transport continuity: startup delay and rebuffer events can change even when all rows eventually complete.

## Data

- CSV: `data/chrome-h3-rebinding-buffered-media-control-20260629.csv`
