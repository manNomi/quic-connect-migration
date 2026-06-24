# Chrome H3 Local UDP Rebinding Repetition Summary

Generated: `2026-06-24`

This summary aggregates local Chrome forced-H3 UDP rebinding proxy repetitions. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Aggregate

| field | value |
| --- | --- |
| runs | `6` |
| status counts | `{'PASS': 6}` |
| heartbeat counts | `{'heartbeat': 3, 'noheartbeat': 3}` |
| classification counts | `{'nat_rebinding_multiple_quic_sessions': 3, 'nat_rebinding_path_validation_without_observed_tuple_change': 3}` |
| heartbeat/classification counts | `{'heartbeat::nat_rebinding_multiple_quic_sessions': 3, 'noheartbeat::nat_rebinding_path_validation_without_observed_tuple_change': 3}` |

## Runs

| run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH_CHALLENGE/PATH_RESPONSE | proxy switched |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| noheartbeat-r1 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | true |
| noheartbeat-r2 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | true |
| noheartbeat-r3 | noheartbeat | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | true |
| heartbeat-r1 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | true |
| heartbeat-r2 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | true |
| heartbeat-r3 | heartbeat | PASS | `nat_rebinding_multiple_quic_sessions` | 2 | 2 | 1/1 | true |

## Interpretation Boundary

Use these rows as repeated local controls for session-attribution risk. They strengthen the claim that server tuple/path-validation evidence must be paired with browser session-continuity evidence, but they do not complete the final controlled-public browser handover protocol.
