# Final Handover Trial Artifact Bundle Check

Generated: `2026-07-01`

## Summary

| field | value |
| --- | --- |
| trial selected | `yes` |
| trial_id | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| browser | `Chrome` |
| phase | `active-network-change` |
| artifact dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| artifact bundle complete | `yes` |
| registration ready | `no` |
| validation claim strength | `negative_control_record_only` |

## Artifact Checks

| role | path | kind | present | matches | bytes | detail |
| --- | --- | --- | --- | ---: | ---: | --- |
| server result | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/server.json` | `file` | `yes` | 1 | 2761 | `file_exists` |
| server qlog directory | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/qlog` | `directory` | `yes` | 2 | 90979 | `directory_has_files` |
| public origin readiness | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/public-origin-readiness.json` | `file` | `yes` | 1 | 781 | `file_exists` |
| classifier summary | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/controlled-public-h3-network-change-summary.json` | `file` | `yes` | 1 | 6252 | `file_exists` |
| network-change command record | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/network-change.json` | `file` | `yes` | 1 | 125 | `file_exists` |
| client path-change summary | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/client-path-change-summary.json` | `file` | `yes` | 1 | 1298 | `file_exists` |
| Chrome network-change NetLog | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/chrome/network-change-netlog.json` | `file` | `yes` | 1 | 29542102 | `file_exists` |

## Validation

- available: `yes`
- counts toward final protocol: `no`
- matched requirements: `-`
- error: `-`

## Blockers

- -
