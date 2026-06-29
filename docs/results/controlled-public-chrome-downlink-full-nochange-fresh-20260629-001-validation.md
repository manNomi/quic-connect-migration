# Final Handover Trial Artifact Validation

Validated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` |
| artifact_dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` |
| summary_path | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001/results/controlled-public-h3-baseline-summary.json` |
| summary status | `PASS` |
| summary classification | `controlled_public_application_h3_confirmed` |
| csv fields complete | `yes` |
| appendable to experiment-results | `yes` |
| counts toward final protocol | `no` |
| claim strength | `record_only_not_final_counting` |

## Matched Requirements

- -

## Warnings

- draft row does not match any final browser handover requirement

## Draft CSV Row

```csv
trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
controlled-public-chrome-downlink-full-nochange-fresh-20260629-001,2026-06-29,PASS,Chrome + controlled public quic-go H3,controlled public browser no-change baseline,HTTP/3 over QUIC,no network change; controlled public downlink streaming without heartbeat,false,true,GET /browser-downlink then streaming GET /downlink-stream,true,false,none,repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-full-nochange-fresh-20260629-001,classification controlled_public_application_h3_confirmed; no_path_change_baseline; client_path_change=-; client_path_eventual_change=-; server remote addr count 5; qlog path validation=false
```
