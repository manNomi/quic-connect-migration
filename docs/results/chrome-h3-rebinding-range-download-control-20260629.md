# Chrome H3 Rebinding Range Download Control

Generated: `2026-06-29`

## Scope

This report summarizes local Chrome forced-H3 byte-range download workloads under UDP rebinding and transient server-to-client packet loss. It models resumable large-download recovery. These rows are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Grouped Result

| profile | drop window | retry | PASS/runs | range complete | retry used | median elapsed ms | median error ms | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| range-resumable-download | 6000ms | 0 | 1/3 | 1/3 | 0/3 | 12186 | 6922 | 1-2 | browser_h3_request_failed=2; nat_rebinding_multiple_quic_sessions=1 |
| range-resumable-download | 6000ms | 2 | 3/3 | 3/3 | 2/3 | 15011 | - | 2-2 | nat_rebinding_multiple_quic_sessions=3 |

## Run Detail

| profile | trial | drop | retry | status | classification | complete | bytes | retries used | elapsed ms | error ms | Chrome sessions | qlog C/R | dropped A/B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| range-resumable-download | chrome-h3-rebinding-range-rep1-drop6000-retry0-20260629 | 6000ms | 0 | PASS | nat_rebinding_multiple_quic_sessions | true | 1048576/1048576 | 0 | 12186 | - | 2 | 7/4 | 58/6 |
| range-resumable-download | chrome-h3-rebinding-range-rep2-drop6000-retry0-20260629 | 6000ms | 0 | FAIL | browser_h3_request_failed | - | 0/1048576 | - | - | 6921 | 1 | 7/3 | 61/7 |
| range-resumable-download | chrome-h3-rebinding-range-rep3-drop6000-retry0-20260629 | 6000ms | 0 | FAIL | browser_h3_request_failed | - | 0/1048576 | - | - | 6923 | 1 | 7/3 | 62/7 |
| range-resumable-download | chrome-h3-rebinding-range-rep1-drop6000-retry2-20260629 | 6000ms | 2 | PASS | nat_rebinding_multiple_quic_sessions | true | 1048576/1048576 | 0 | 12314 | - | 2 | 7/4 | 56/6 |
| range-resumable-download | chrome-h3-rebinding-range-rep2-drop6000-retry2-20260629 | 6000ms | 2 | PASS | nat_rebinding_multiple_quic_sessions | true | 1048576/1048576 | 1 | 15011 | - | 2 | 7/3 | 61/7 |
| range-resumable-download | chrome-h3-rebinding-range-rep3-drop6000-retry2-20260629 | 6000ms | 2 | PASS | nat_rebinding_multiple_quic_sessions | true | 1048576/1048576 | 1 | 15030 | - | 2 | 7/3 | 62/7 |

## Interpretation Boundary

A completed range row is resumable application-level download continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to compare recovery semantics: a full-stream retry restarts a long response, while byte-range retry can resume from the failed chunk. Both still need session attribution before being called QUIC CM.

## Data

- CSV: `data/chrome-h3-rebinding-range-download-control-20260629.csv`
