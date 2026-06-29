# Final Handover Trial Artifact Validation

Validated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` |
| artifact_dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-network-change-20260629-001` |
| summary_path | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-network-change-20260629-001/results/controlled-public-h3-network-change-summary.json` |
| summary status | `PASS_NEGATIVE_CONTROL` |
| summary classification | `no_client_active_path_change_observed` |
| csv fields complete | `yes` |
| appendable to experiment-results | `yes` |
| counts toward final protocol | `no` |
| claim strength | `negative_control_record_only` |

## Matched Requirements

- -

## Warnings

- draft row does not match any final browser handover requirement
- negative-control row is appendable but must not be claimed as CM success
- application_success is not true
- client path snapshot did not show active path change

## Draft CSV Row

```csv
trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
controlled-public-chrome-downlink-heartbeat-network-change-20260629-001,2026-06-29,PASS_NEGATIVE_CONTROL,Chrome + controlled public quic-go H3,controlled public browser active network-change,HTTP/3 over QUIC,active path change during Chrome downlink workload; NETWORK_CHANGE_CMD executed,false,false,GET /browser-downlink then streaming GET /downlink-stream plus GET /heartbeat,false,false,no_client_active_path_change_observed,repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-network-change-20260629-001,classification no_client_active_path_change_observed; heartbeat variant; client_path_change=interface_set_changed_without_route_change; client_path_eventual_change=interface_set_changed_without_route_change; server remote addr count 4; qlog path validation=false; target h3 remote addr count 1
```
