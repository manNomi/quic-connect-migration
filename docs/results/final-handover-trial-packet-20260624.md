# Final Handover Trial Packet

Generated: `2026-06-30`

## Summary

| field | value |
| --- | --- |
| state | `blocked_by_readiness` |
| public-safe default | `yes` |
| sensitive values redacted | `no` |
| next trial ready | `no` |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next browser | `Chrome` |
| next phase | `active-network-change` |
| final completion | `3/6` |

## Missing Required Gates

- baseline_summary_ready
- network_change_command_present
- desktop_path_change_ready

## Final Protocol Blockers

- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- p1-safari-or-android-feasibility: 0/1

## Preflight Commands

```bash
python3 tools/check_controlled_public_config.py --require-baseline-ready
python3 tools/select_next_final_handover_trial.py --output docs/results/final-handover-next-trial-20260624.md
python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md
python3 tools/build_final_handover_operator_checklist.py --output docs/results/final-handover-operator-checklist-20260624.md
```

## Trial

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| requirement | `chrome-downlink-noheartbeat-active-cm` |
| workload | `browser-downlink active path change` |
| heartbeat | `false` |
| expected requests | `2` |
| artifact dir | `artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| claim gate | `classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true` |

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=2 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

Expected artifacts:

| role | path |
| --- | --- |
| server result | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/server.json` |
| server qlog directory | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/qlog` |
| public origin readiness | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/public-origin-readiness.json` |
| classifier summary | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/controlled-public-h3-network-change-summary.json` |
| network-change command record | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/network-change.json` |
| client path-change summary | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/results/client-path-change-summary.json` |
| Chrome network-change NetLog | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001/chrome/network-change-netlog.json` |

## Post-Trial Registration

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 --require-final-countable --require-complete
python3 tools/validate_final_handover_trial_artifact.py --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 --require-final-countable
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 --require-final-countable --require-artifact-bundle --output /tmp/final-handover-append-dry-run.md
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-downlink-noheartbeat-network-change-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 --require-final-countable --require-artifact-bundle --apply
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md
python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md
python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md
```
