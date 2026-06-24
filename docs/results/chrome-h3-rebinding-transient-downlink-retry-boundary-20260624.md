# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'PASS': 6}` |
| status by drop window | `{'6000ms': {'PASS': 3}, '9000ms': {'PASS': 3}}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 3, 'nat_rebinding_path_validation_without_observed_tuple_change': 3}` |
| application complete | `6/6` |
| proxy switched | `6/6` |
| total dropped A-side server packets | `547` |
| total dropped B-side server packets | `41` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-downlink-1m-drop-ab-6000ms | downlink | 1x/500ms | 0 | 6000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 15954 | - | 2 | 1 | 2/1 | 73/1 | 4173 | 39/107 | 124/762 | - |
| rep01-downlink-1m-drop-ab-9000ms | downlink | 1x/500ms | 0 | 9000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 21713 | - | 2 | 1 | 2/1 | 80/1 | 6641 | 37/111 | 129/779 | - |
| rep02-downlink-1m-drop-ab-6000ms | downlink | 1x/500ms | 1 | 6000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15487 | - | 3 | 2 | 7/3 | 104/7 | 5102 | 39/168 | 115/790 | - |
| rep02-downlink-1m-drop-ab-9000ms | downlink | 1x/500ms | 1 | 9000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 19693 | - | 3 | 2 | 7/3 | 105/24 | 8929 | 37/306 | 102/926 | - |
| rep03-downlink-1m-drop-ab-6000ms | downlink | 1x/500ms | 1 | 6000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | 15491 | - | 3 | 2 | 7/3 | 106/7 | 5182 | 37/172 | 114/790 | - |
| rep03-downlink-1m-drop-ab-9000ms | downlink | 1x/500ms | 0 | 9000ms | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 19104 | - | 2 | 1 | 2/1 | 79/1 | 5524 | 37/111 | 106/790 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: inconclusive because the sweep does not contain both PASS and FAIL windows.
