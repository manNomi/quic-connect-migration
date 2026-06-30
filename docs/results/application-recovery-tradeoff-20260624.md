# Application Recovery Tradeoff

Generated: `2026-06-30`

This synthesis combines the Chrome forced-H3 local UDP rebinding upload-only boundary controls. It is an application recovery table, not a browser connection migration success table.

## Source CSVs

- `data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv` (no-retry upload fine boundary)
- `data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv` (no-retry upload 4750ms replication)
- `data/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.csv` (one-retry upload boundary)
- `data/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.csv` (one-retry long outage)
- `data/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.csv` (one-retry stress boundary)
- `data/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.csv` (two-retry 15000ms recovery)
- `data/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.csv` (two-retry stress boundary)

## Boundary Summary

| retry budget | latest all-pass window | mixed window | first later all-fail window | latency at latest all-pass | Chrome QUIC sessions | error timing at fail |
| --- | --- | --- | --- | --- | --- | --- |
| 0 retry | 4600ms | 4750ms | 4900ms | 10215-10230ms | 1-1 | 6919-6922ms |
| 1 retry | 12000ms | - | 15000ms | 19978-19984ms | 3-3 | 15936-15943ms |
| 2 retry | 18000ms | - | 21000ms | 28196-28199ms | 4-4 | 20950-20955ms |

## Detailed Groups

| retry | drop window | PASS/runs | app complete | complete ms | error ms | Chrome sessions | upload attempts | upload bytes | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0x/0ms | 4600ms | 3/3 | 3 | 10215-10230ms | - | 1-1 | 1-1 | 1048576-1048576 | nat_rebinding_path_validation_without_observed_tuple_change=3 |
| 0x/0ms | 4750ms | 3/6 | 3 | 10466-11261ms | 6917-6921ms | 1-2 | 1-1 | 0-1048576 | browser_application_task_failed=3; nat_rebinding_path_validation_without_observed_tuple_change=3 |
| 0x/0ms | 4900ms | 0/3 | 0 | - | 6919-6922ms | 2-2 | 1-1 | 0-0 | browser_application_task_failed=3 |
| 0x/0ms | 5000ms | 0/3 | 0 | - | 6917-6920ms | 2-2 | 1-1 | 0-0 | browser_application_task_failed=3 |
| 1x/1000ms | 4900ms | 3/3 | 3 | 15470-15476ms | - | 2-2 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 1x/1000ms | 5000ms | 3/3 | 3 | 15463-15468ms | - | 2-2 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 1x/1000ms | 6000ms | 3/3 | 3 | 15465-15469ms | - | 2-3 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 1x/1000ms | 9000ms | 3/3 | 3 | 19671-19679ms | - | 2-3 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 1x/1000ms | 12000ms | 3/3 | 3 | 19978-19984ms | - | 3-3 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 1x/1000ms | 15000ms | 0/3 | 0 | - | 15936-15943ms | 3-3 | 1-1 | 0-0 | browser_h3_request_failed=3 |
| 2x/1000ms | 15000ms | 3/3 | 3 | 24484-24503ms | - | 4-4 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 2x/1000ms | 18000ms | 3/3 | 3 | 28196-28199ms | - | 4-4 | 2-2 | 1048576-1048576 | nat_rebinding_multiple_quic_sessions=3 |
| 2x/1000ms | 21000ms | 0/3 | 0 | - | 20950-20955ms | 4-4 | 1-1 | 0-0 | browser_application_task_failed=3 |

## Interpretation

- No-retry upload completion is stable through 4600ms, mixed at 4750ms, and repeatedly fails from 4900ms in this curated local boundary set.
- One application-level retry moves the repeated-pass region through 12000ms but fails repeatedly at 15000ms.
- Two application-level retries recover 15000ms and 18000ms but fail repeatedly at 21000ms.
- Retry budget increases user-visible task recovery, but the successful retry rows use replacement/multiple Chrome QUIC sessions and increasing completion latency; this must not be reported as single-session browser CM success.
