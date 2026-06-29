# Final Handover Trial Artifact Validation

Validated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-fresh-origin-smoke-20260629-005` |
| artifact_dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-fresh-origin-smoke-20260629-005` |
| summary_path | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-fresh-origin-smoke-20260629-005/results/controlled-public-h3-baseline-summary.json` |
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
controlled-public-chrome-fresh-origin-smoke-20260629-005,2026-06-29,PASS,Chrome + controlled public quic-go H3,controlled public browser baseline,HTTP/3 over QUIC,controlled public application H3 baseline; no active path-change,false,true,GET /browser-slow plus streaming GET /slow-js,true,false,none,repro/quic-go-min-repro/artifacts/controlled-public-chrome-fresh-origin-smoke-20260629-005,classification controlled_public_application_h3_confirmed; controlled_public_application_h3_confirmed; controlled_public_server_qlog_h3_confirmed; client_path_change=-; client_path_eventual_change=-; server remote addr count 4; qlog path validation=false
```
