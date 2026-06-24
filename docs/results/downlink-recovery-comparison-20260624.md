# Downlink Recovery Comparison

Generated: `2026-06-24`

This synthesis compares local Chrome forced-H3 downlink wait-only and one-retry controls under the same 6000ms/9000ms A+B return-path outage windows. It is local recovery evidence, not public browser handover evidence.

## Comparison

| policy | drop window | PASS/runs | app complete | retries used | complete ms | error ms | Chrome sessions | classification |
| --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |
| wait_only_no_retry | 6000ms | 0/3 | 0 | `-=3` | - | 6926-6931 | 1-1 | `browser_application_task_failed=3` |
| wait_only_no_retry | 9000ms | 0/3 | 0 | `-=3` | - | 6923-6935 | 1-1 | `browser_application_task_failed=3` |
| retry_enabled_1x500ms | 6000ms | 3/3 | 3 | `0=1; 1=2` | 15487-15954 | - | 1-2 | `nat_rebinding_multiple_quic_sessions=2; nat_rebinding_path_validation_without_observed_tuple_change=1` |
| retry_enabled_1x500ms | 9000ms | 3/3 | 3 | `0=2; 1=1` | 19104-21713 | - | 1-2 | `nat_rebinding_multiple_quic_sessions=1; nat_rebinding_path_validation_without_observed_tuple_change=2` |

## Interpretation

- Wait-only no-retry rows fail even with the longer hold/grace timing used by the retry control.
- The retry-enabled rows complete, but completion mechanism is mixed: some rows complete without consuming the retry, while others use one retry and create multiple Chrome target QUIC sessions.
- Therefore downlink recovery must be reported as application-level recovery and retransmission/session-management behavior, not as single-session browser connection migration success.
