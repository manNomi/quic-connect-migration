# Polling Transition-Zone Synthesis

Generated: `2026-06-24`

This synthesis combines the Chrome forced-H3 local UDP rebinding polling/dashboard controls. It is a dashboard-like repeated fetch continuity summary, not public browser handover evidence.

## Source CSVs

- `data/chrome-h3-rebinding-transient-poll-boundary-20260624.csv` (poll short boundary)
- `data/chrome-h3-rebinding-transient-poll-long-boundary-20260624.csv` (poll long boundary)
- `data/chrome-h3-rebinding-transient-poll-4000-replication-20260625.csv` (poll 4000ms replication)

## Grouped Evidence

| drop window | PASS/runs | app complete | server requests | Chrome sessions | qlog PATH_CHALLENGE | qlog PATH_RESPONSE | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 250ms | 3/3 | 3 | 7-7 | 2-2 | 0-0 | 0-0 | nat_rebinding_multiple_quic_sessions=3 |
| 1500ms | 3/3 | 3 | 7-7 | 2-2 | 0-0 | 0-0 | nat_rebinding_multiple_quic_sessions=3 |
| 3000ms | 3/3 | 3 | 7-7 | 2-2 | 0-0 | 0-0 | nat_rebinding_multiple_quic_sessions=3 |
| 4000ms | 1/6 | 1 | 2-7 | 2-3 | 0-7 | 0-4 | browser_application_task_failed=5; nat_rebinding_multiple_quic_sessions=1 |
| 6000ms | 0/3 | 0 | 2-2 | 2-2 | 0-0 | 0-0 | browser_application_task_failed=3 |
| 9000ms | 0/3 | 0 | 2-2 | 2-2 | 0-0 | 0-0 | browser_application_task_failed=3 |

## Interpretation

- The polling workload completed 9/9 through 3000ms in the short-boundary control.
- At 4000ms the result remains a transition-zone result: 1/6 PASS and 5/6 FAIL.
- At 6000ms and 9000ms it repeatedly failed: 6/6 FAIL.
- PASS rows still used two Chrome target QUIC sessions, so polling completion is not single-session browser CM evidence.
- Use this table to justify dashboard recovery as a separate application-level metric that must be reported with session attribution.
