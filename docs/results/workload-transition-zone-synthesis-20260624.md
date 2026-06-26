# Workload Transition-Zone Synthesis

Generated: `2026-06-26`

This synthesis combines the Chrome forced-H3 local UDP rebinding downlink and upload fine-boundary controls. It compares DOM task completion across workload direction; it is not public browser handover evidence.

## Source CSVs

- `data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv` (downlink fine boundary)
- `data/chrome-h3-rebinding-transient-downlink-5000-5500-replication-20260625.csv` (downlink 5000/5500ms replication)
- `data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv` (upload fine boundary)
- `data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv` (upload 4750ms replication)

## Grouped Evidence

| workload | drop window | PASS/runs | app complete | complete ms | error ms | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| downlink | 5000ms | 5/6 | 5 | 12126-13411ms | 6922-6922ms | 1-1 | browser_application_task_failed=1; nat_rebinding_path_validation_without_observed_tuple_change=5 |
| downlink | 5500ms | 4/6 | 4 | 12626-14114ms | 6923-6950ms | 1-1 | browser_application_task_failed=2; nat_rebinding_path_validation_without_observed_tuple_change=4 |
| downlink | 6000ms | 0/3 | 0 | - | 6923-6927ms | 1-1 | browser_application_task_failed=3 |
| upload | 4600ms | 3/3 | 3 | 10215-10230ms | - | 1-1 | nat_rebinding_path_validation_without_observed_tuple_change=3 |
| upload | 4750ms | 3/6 | 3 | 10466-11261ms | 6917-6921ms | 1-2 | browser_application_task_failed=3; nat_rebinding_path_validation_without_observed_tuple_change=3 |
| upload | 4900ms | 0/3 | 0 | - | 6919-6922ms | 2-2 | browser_application_task_failed=3 |
| upload | 5000ms | 0/3 | 0 | - | 6917-6920ms | 2-2 | browser_application_task_failed=3 |

## Interpretation

- Downlink remains mixed at 5000ms (5/6 PASS) and 5500ms (4/6 PASS), then repeatedly fails at 6000ms (0/3 PASS).
- Upload is stable at 4600ms (3/3 PASS), remains mixed at 4750ms (3/6 PASS), and repeatedly fails at 4900ms/5000ms (0/3 and 0/3 PASS).
- Workload direction changes the transition zone; a single outage-duration threshold would hide this behavior.
- qlog path evidence appears in both PASS and FAIL rows, so transport evidence and DOM task completion must remain separate outcomes.
