# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-25`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `3` |
| status counts | `{'FAIL': 1, 'PASS': 2}` |
| status by drop window | `{'4750ms': {'FAIL': 1, 'PASS': 2}}` |
| classification counts | `{'browser_application_task_failed': 1, 'nat_rebinding_path_validation_without_observed_tuple_change': 2}` |
| application complete | `2/3` |
| proxy switched | `3/3` |
| total dropped A-side server packets | `162` |
| total dropped B-side server packets | `18` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-upload-1m-drop-ab-4750ms | upload | 0x/500ms | 0 | 4750ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10466 | - | 2 | 1 | 7/4 | 58/6 | 3859 | 68/853 | 35/132 | 1048576 |
| rep02-upload-1m-drop-ab-4750ms | upload | 0x/500ms | 0 | 4750ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 10493 | - | 2 | 2 | 7/4 | 50/6 | 4690 | 72/854 | 45/107 | 1048576 |
| rep03-upload-1m-drop-ab-4750ms | upload | 0x/500ms |  | 4750ms | FAIL | `browser_application_task_failed` | false | - | 6920 | 2 | 2 | 6/3 | 54/6 | 4667 | 65/89 | 30/14 | 0 |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: PASS and FAIL windows overlap or are non-monotonic; inspect per-row evidence before drawing a threshold.
