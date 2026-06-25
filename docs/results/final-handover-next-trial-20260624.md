# Final Handover Next Trial

Generated: `2026-06-25`

## Summary

| field | value |
| --- | --- |
| experiments | `data/experiment-results.csv` |
| config source | `local config (redacted)` |
| public-safe default | `yes` |
| sensitive values redacted | `yes` |
| final protocol complete | `no` |
| complete requirements | `2/6` |
| existing trial rows | `68` |
| planned trial executions | `10` |

## Blockers

- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-nochange-baseline: 0/1
- p1-safari-or-android-feasibility: 0/1

## Next Trial

| field | value |
| --- | --- |
| queue index | `3` |
| trial_id | `controlled-public-chrome-downlink-heartbeat-nochange-001` |
| requirement | `chrome-downlink-heartbeat-nochange-baseline` |
| phase | `no-change-baseline` |
| browser | `Chrome` |
| workload | `browser-downlink no network change` |
| heartbeat | `true` |
| expected requests | `6` |
| artifact dir | `artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001` |
| claim gate | `no active network-change command; server/browser workload completes; classification no_path_change_baseline` |

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
PUBLIC_ORIGIN_HOST=<redacted-public-origin-host> \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=<redacted-tls-cert-file> \
TLS_KEY_FILE=<redacted-tls-key-file> \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=6 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
PUBLIC_ORIGIN_URL='https://<redacted-public-origin-host>/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
SECOND_URL='https://<redacted-public-origin-host>/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=6 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

Post-trial registration commands:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id controlled-public-chrome-downlink-heartbeat-nochange-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 --require-final-countable --require-complete
python3 tools/validate_final_handover_trial_artifact.py --trial-id controlled-public-chrome-downlink-heartbeat-nochange-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 --require-final-countable
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-downlink-heartbeat-nochange-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 --require-final-countable --require-artifact-bundle --output /tmp/final-handover-append-dry-run.md
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-downlink-heartbeat-nochange-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 --require-final-countable --require-artifact-bundle --apply
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
```
