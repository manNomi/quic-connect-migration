# Workload Transition-Zone Synthesis

Generated: `2026-06-25`

This synthesis combines the Chrome forced-H3 local UDP rebinding downlink and upload fine-boundary controls. It compares DOM task completion across workload direction; it is not public browser handover evidence.

## Source CSVs

- `data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv` (downlink fine boundary)
- `data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv` (upload fine boundary)

## Grouped Evidence

| workload | drop window | PASS/runs | app complete | complete ms | error ms | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| downlink | 5000ms | 2/3 | 2 | 12276-13411ms | 6922-6922ms | 1-1 | browser_application_task_failed=1; nat_rebinding_path_validation_without_observed_tuple_change=2 |
| downlink | 5500ms | 2/3 | 2 | 13840-14114ms | 6923-6923ms | 1-1 | browser_application_task_failed=1; nat_rebinding_path_validation_without_observed_tuple_change=2 |
| downlink | 6000ms | 0/3 | 0 | - | 6923-6927ms | 1-1 | browser_application_task_failed=3 |
| upload | 4600ms | 3/3 | 3 | 10215-10230ms | - | 1-1 | nat_rebinding_path_validation_without_observed_tuple_change=3 |
| upload | 4750ms | 1/3 | 1 | 11261-11261ms | 6917-6921ms | 1-2 | browser_application_task_failed=2; nat_rebinding_path_validation_without_observed_tuple_change=1 |
| upload | 4900ms | 0/3 | 0 | - | 6919-6922ms | 2-2 | browser_application_task_failed=3 |
| upload | 5000ms | 0/3 | 0 | - | 6917-6920ms | 2-2 | browser_application_task_failed=3 |

## Interpretation

- Downlink is mixed at 5000ms and 5500ms, then repeatedly fails at 6000ms in this local fine-boundary set.
- Upload is stable at 4600ms, mixed at 4750ms, and repeatedly fails from 4900ms.
- Workload direction changes the transition zone; a single outage-duration threshold would hide this behavior.
- qlog path evidence appears in both PASS and FAIL rows, so transport evidence and DOM task completion must remain separate outcomes.
