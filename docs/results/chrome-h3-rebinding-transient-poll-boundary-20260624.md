# Chrome H3 Local Rebinding Transient Return-Path Sweep

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.

## Aggregate

| field | value |
| --- | --- |
| runs | `9` |
| status counts | `{'PASS': 9}` |
| status by drop window | `{'250ms': {'PASS': 3}, '1500ms': {'PASS': 3}, '3000ms': {'PASS': 3}}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 9}` |
| application complete | `9/9` |
| proxy switched | `9/9` |
| total dropped A-side server packets | `0` |
| total dropped B-side server packets | `117` |

## Runs

| profile | workload | retry | used | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |
| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| rep01-poll-1m-drop-ab-250ms | poll | 0x/500ms |  | 250ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/8 | 233 | 15/174 | 35/169 | - |
| rep01-poll-1m-drop-ab-1500ms | poll | 0x/500ms |  | 1500ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/14 | 1005 | 12/740 | 33/732 | - |
| rep01-poll-1m-drop-ab-3000ms | poll | 0x/500ms |  | 3000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/17 | 2005 | 13/133 | 33/128 | - |
| rep02-poll-1m-drop-ab-250ms | poll | 0x/500ms |  | 250ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/8 | 233 | 12/210 | 29/205 | - |
| rep02-poll-1m-drop-ab-1500ms | poll | 0x/500ms |  | 1500ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/14 | 1004 | 15/696 | 35/689 | - |
| rep02-poll-1m-drop-ab-3000ms | poll | 0x/500ms |  | 3000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/17 | 2003 | 15/161 | 35/152 | - |
| rep03-poll-1m-drop-ab-250ms | poll | 0x/500ms |  | 250ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/8 | 236 | 12/175 | 33/171 | - |
| rep03-poll-1m-drop-ab-1500ms | poll | 0x/500ms |  | 1500ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/14 | 1004 | 12/709 | 33/700 | - |
| rep03-poll-1m-drop-ab-3000ms | poll | 0x/500ms |  | 3000ms | PASS | `nat_rebinding_multiple_quic_sessions` | true | - | - | 7 | 2 | 0/0 | 0/17 | 2005 | 15/160 | 35/156 | - |

## Interpretation Boundary

Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.

Observed local boundary: inconclusive because the sweep does not contain both PASS and FAIL windows.
