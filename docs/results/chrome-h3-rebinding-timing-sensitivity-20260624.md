# Chrome H3 Local Rebinding Timing Sensitivity Summary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding runs with early and late proxy switch timing. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Aggregate

| field | value |
| --- | --- |
| runs | `12` |
| status counts | `{'PASS': 12}` |
| workload counts | `{'downlink': 8, 'upload': 4}` |
| timing counts | `{'early': 6, 'late': 6}` |
| packet rebinding observed | `12/12` |
| qlog path validation observed | `12/12` |
| NetLog target path validation observed | `12/12` |

## Timing Groups

| workload | timing | rebind after | runs | status counts | classification counts | heartbeat counts | qlog path validation | NetLog target path validation | packet rebind | avg B packet share |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: |
| downlink | early | 500ms | 4 | `{'PASS': 4}` | `{'nat_rebinding_multiple_quic_sessions': 2, 'nat_rebinding_path_validation_without_observed_tuple_change': 2}` | `{'heartbeat': 2, 'noheartbeat': 2}` | 4/4 | 4/4 | 4/4 | 0.618 |
| downlink | late | 5s | 4 | `{'PASS': 4}` | `{'nat_rebinding_path_validation_without_observed_tuple_change': 4}` | `{'heartbeat': 2, 'noheartbeat': 2}` | 4/4 | 4/4 | 4/4 | 0.172 |
| upload | early | 500ms | 2 | `{'PASS': 2}` | `{'nat_rebinding_path_validation_without_observed_tuple_change': 2}` | `{'n/a': 2}` | 2/2 | 2/2 | 2/2 | 0.800 |
| upload | late | 5s | 2 | `{'PASS': 2}` | `{'nat_rebinding_path_validation_without_observed_tuple_change': 2}` | `{'n/a': 2}` | 2/2 | 2/2 | 2/2 | 0.181 |

## Runs

| workload | timing | run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH C/R | NetLog target PATH C/R | proxy packets A/B | B packet share | upload bytes |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| downlink | early | noheartbeat-r1 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 13/28 | 0.683 | - |
| downlink | early | noheartbeat-r2 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 17/26 | 0.605 | - |
| downlink | early | heartbeat-r1 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | 1/1 | 16/25 | 0.610 | - |
| downlink | early | heartbeat-r2 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | 1/1 | 17/23 | 0.575 | - |
| downlink | late | noheartbeat-r1 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 30/9 | 0.231 | - |
| downlink | late | noheartbeat-r2 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 33/9 | 0.214 | - |
| downlink | late | heartbeat-r1 | heartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 2 | 1/1 | 1/1 | 32/5 | 0.135 | - |
| downlink | late | heartbeat-r2 | heartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 2 | 1/1 | 1/1 | 33/4 | 0.108 | - |
| upload | early | upload-r1 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 49/197 | 0.801 | 262144 |
| upload | early | upload-r2 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 49/196 | 0.800 | 262144 |
| upload | late | upload-r1 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 200/46 | 0.187 | 262144 |
| upload | late | upload-r2 | n/a | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 202/43 | 0.176 | 262144 |

## Interpretation Boundary

All timing-sensitivity rows completed and recorded proxy packet rebinding, qlog path validation, and Chrome target NetLog path-validation frames. Early rebinding shifts more packets to upstream B, while late rebinding leaves fewer B-side packets but still produces path-validation evidence. The heartbeat rows show that workload timing can change whether extra request/session evidence appears, so heartbeat-based recovery must be evaluated with browser session attribution rather than tuple counts alone.

These rows strengthen the local NAT-rebinding evidence boundary. They still do not complete the controlled-public active browser handover protocol because no real client route/interface/public-IP change is present.
