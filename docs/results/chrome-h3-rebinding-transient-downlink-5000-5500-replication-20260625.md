# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-25`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'FAIL': 1, 'PASS': 5}` |
| status by drop window | `{'5000ms': {'PASS': 3}, '5500ms': {'FAIL': 1, 'PASS': 2}}` |
| classification counts | `{'browser_application_task_failed': 1, 'nat_rebinding_path_validation_without_observed_tuple_change': 5}` |
| application complete | `5/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `571` |
| total dropped B-side server packets | `32` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 0 | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12559 | - | 2 | 1 | 7/4 | 102/6 | 3993 | 41/116 | 117/764 | - |
| rep01-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms |  | 5500ms | FAIL | `browser_application_task_failed` | false | - | 6950 | 2 | 1 | 6/3 | 99/6 | 4649 | 38/30 | 114/0 | - |
| rep02-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 0 | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 13026 | - | 2 | 1 | 8/4 | 103/7 | 4982 | 38/130 | 168/756 | - |
| rep02-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms | 0 | 5500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12626 | - | 2 | 1 | 7/4 | 98/6 | 4026 | 39/125 | 115/757 | - |
| rep03-downlink-1m-drop-ab-5000ms | downlink | 0x/500ms | 0 | 5000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 12126 | - | 2 | 1 | 7/4 | 102/6 | 3797 | 41/115 | 117/763 | - |
| rep03-downlink-1m-drop-ab-5500ms | downlink | 0x/500ms | 0 | 5500ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 14079 | - | 2 | 1 | 2/1 | 67/1 | 2832 | 39/106 | 136/692 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: PASS and FAIL windows overlap or are non-monotonic; inspect per-row evidence before drawing a threshold.
