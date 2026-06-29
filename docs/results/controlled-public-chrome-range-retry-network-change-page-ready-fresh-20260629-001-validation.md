# Final Handover Trial Artifact Validation

Validated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` |
| artifact_dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` |
| summary_path | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001/results/controlled-public-h3-network-change-summary.json` |
| summary status | `PASS_NEGATIVE_CONTROL` |
| summary classification | `tuple_changed_without_path_validation` |
| csv fields complete | `yes` |
| appendable to experiment-results | `yes` |
| counts toward final protocol | `no` |
| claim strength | `negative_control_record_only` |

## Matched Requirements

- -

## Warnings

- draft row does not match any final browser handover requirement
- negative-control row is appendable but must not be claimed as CM success
- tuple change without qlog path validation excludes CM success

## Draft CSV Row

```csv
trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001,2026-06-29,PASS_NEGATIVE_CONTROL,Chrome + controlled public quic-go H3,controlled public browser active network-change,HTTP/3 over QUIC,active path change during Chrome byte-range download workload; NETWORK_CHANGE_CMD executed,false,true,GET /browser-range-download plus byte-range GET /range-download,true,false,path-validation-not-observed,repro/quic-go-min-repro/artifacts/controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001,classification tuple_changed_without_path_validation; client_path_change=client_active_path_changed; client_path_eventual_change=no_client_path_change_observed; server remote addr count 5; qlog path validation=false; target h3 remote addr count 2
```
