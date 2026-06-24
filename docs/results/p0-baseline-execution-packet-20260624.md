# P0 Baseline Execution Packet

Generated: `2026-06-24`

This packet is public-safe. It orders the next controlled-public Chrome baseline from private config setup through artifact validation without printing private domains, TLS paths, or network-change commands.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-h3-baseline-001` |
| next phase | `baseline` |
| next trial ready | `no` |
| packet state | `blocked_by_readiness` |
| needed-now gates | `controlled_public_config_present; public_origin_host_configured; public_origin_url_configured; tls_config_present` |

## Ordered Stages

| stage | order | status | owner | action | command | stop condition |
| --- | --- | --- | --- | --- | --- | --- |
| 0-private-config | 1 | `blocked` | operator | Create and fill the ignored controlled-public origin config. | `cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env && $EDITOR harness/config/controlled-public-origin.env` | stop until needed-now gates are cleared |
| 1-preflight | 2 | `blocked` | operator | Run baseline readiness checks before starting server/client artifacts. | `python3 tools/check_controlled_public_config.py --require-baseline-ready && python3 tools/select_next_final_handover_trial.py --output docs/results/final-handover-next-trial-20260624.md && python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md && python3 tools/build_final_handover_operator_checklist.py --output docs/results/final-handover-operator-checklist-20260624.md` | stop if any required gate remains missing |
| 2-origin-server | 3 | `blocked` | origin-host | Start the controlled public H3 origin server for the selected baseline trial. | `cd repro/quic-go-min-repro<br>RUN_ID=controlled-public-chrome-h3-baseline-001 \<br>ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \<br>PUBLIC_ORIGIN_HOST=h3.example.com \<br>PUBLIC_ORIGIN_PORT=443 \<br>TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \<br>TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \<br>LISTEN_ADDR=0.0.0.0:443 \<br>TCP_ADDR=0.0.0.0:443 \<br>ALT_SVC='h3=":443"; ma=60' \<br>EXPECTED_REQUESTS=4 \<br>TIMEOUT=300s \<br>COMPLETION_GRACE=2s \<br>./scripts/run-controlled-public-h3-server.sh` | stop if baseline preflight is not ready |
| 3-browser-client | 4 | `blocked` | client-host | Run Chrome baseline navigation and collect NetLog/qlog summaries. | `cd repro/quic-go-min-repro<br>RUN_ID=controlled-public-chrome-h3-baseline-001 \<br>ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \<br>CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \<br>PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \<br>SECOND_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \<br>CONTROLLED_PUBLIC_EXPECTED_REQUESTS=4 \<br>REQUIRE_H3_ALT_SVC=1 \<br>REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \<br>./scripts/run-controlled-public-h3-browser-baseline.sh` | stop if server/origin terminal is not running |
| 4-post-trial-registration | 5 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-complete` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 6 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/validate_final_handover_trial_artifact.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 7 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-artifact-bundle --output /tmp/final-handover-append-dry-run.md` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 8 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-artifact-bundle --apply` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 9 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 10 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 11 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md` | stop if raw artifact bundle or final-countable validation fails |
| 4-post-trial-registration | 12 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate paper/audit outputs. | `python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md` | stop if raw artifact bundle or final-countable validation fails |

## Interpretation

- Run stage 0 and stage 1 first; do not start server/client artifact capture while needed-now gates remain.
- The server/client commands remain public-template commands until the private config is supplied locally.
- After a PASS baseline is registered, regenerate P0 status; the next blocker should move from baseline config to active path-change readiness.
