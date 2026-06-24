# Final Handover Next Trial

Generated: `2026-06-24`

## Summary

| field | value |
| --- | --- |
| experiments | `data/experiment-results.csv` |
| config source | `public template` |
| public-safe default | `yes` |
| final protocol complete | `no` |
| complete requirements | `0/6` |
| existing trial rows | `35` |
| planned trial executions | `10` |

## Blockers

- chrome-controlled-public-application-h3-baseline: 0/1
- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- chrome-downlink-noheartbeat-nochange-baseline: 0/1
- chrome-downlink-heartbeat-nochange-baseline: 0/1
- p1-safari-or-android-feasibility: 0/1

## Next Trial

| field | value |
| --- | --- |
| queue index | `1` |
| trial_id | `controlled-public-chrome-h3-baseline-001` |
| requirement | `chrome-controlled-public-application-h3-baseline` |
| phase | `baseline` |
| browser | `Chrome` |
| workload | `browser-slow application H3 baseline` |
| heartbeat | `n/a` |
| expected requests | `4` |
| artifact dir | `artifacts/controlled-public-chrome-h3-baseline-001` |
| claim gate | `status PASS; controlled_public_application_h3_confirmed; server qlog H3 confirmed` |

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-h3-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=4 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-h3-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
SECOND_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=4 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

Post-trial registration commands:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-complete
python3 tools/validate_final_handover_trial_artifact.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-artifact-bundle --output /tmp/final-handover-append-dry-run.md
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-artifact-bundle --apply
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
```
