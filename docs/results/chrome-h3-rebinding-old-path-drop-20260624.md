# Chrome H3 Local Rebinding Old-Path Drop Summary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs where the proxy drops server-to-client packets arriving on upstream A after client traffic has switched to upstream B. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Aggregate

| field | value |
| --- | --- |
| runs | `11` |
| status counts | `{'PASS': 11}` |
| workload counts | `{'downlink': 7, 'upload': 4}` |
| heartbeat counts | `{'heartbeat': 3, 'n/a': 4, 'noheartbeat': 4}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 3, 'nat_rebinding_path_validation_without_observed_tuple_change': 8}` |
| proxy switched | `11/11` |
| old-path drop enabled | `11/11` |
| qlog path validation | `11/11` |
| NetLog target path validation | `11/11` |
| total dropped A-side server packets | `60` |
| total dropped A-side server bytes | `2814` |

## Runs

| workload | run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH C/R | NetLog target PATH C/R | client packets A/B | server packets A/B | dropped A server packets | upload bytes |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| downlink | chrome-h3-rebinding-drop-oldpath-downlink-20260624 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 17/27 | 26/35 | 0 | - |
| upload | chrome-h3-rebinding-drop-oldpath-upload-20260624 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 2 | 1/1 | 1/1 | 54/198 | 31/49 | 21 | 262144 |
| downlink | noheartbeat-r1 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 17/26 | 27/35 | 0 | - |
| downlink | noheartbeat-r2 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 16/23 | 27/30 | 0 | - |
| downlink | noheartbeat-r3 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 19/28 | 29/38 | 0 | - |
| downlink | heartbeat-r1 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | 1/1 | 16/23 | 27/57 | 0 | - |
| downlink | heartbeat-r2 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | 1/1 | 16/20 | 27/55 | 0 | - |
| downlink | heartbeat-r3 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | 1/1 | 16/24 | 27/58 | 0 | - |
| upload | upload-r1 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 49/198 | 20/80 | 9 | 262144 |
| upload | upload-r2 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 52/198 | 26/68 | 14 | 262144 |
| upload | upload-r3 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 49/198 | 25/66 | 16 | 262144 |

## Interpretation Boundary

Use these rows as local old-path-unavailable controls. Application completion under old-path drop is stronger than tuple-only evidence, but it still does not prove browser handover success. Chrome target QUIC session counts, qlog path validation, proxy packet logs, and actual client path-change evidence remain separate requirements.
