# P0 Baseline Execution Packet

Generated: `2026-06-30`

This packet is public-safe. It orders the next controlled-public Chrome baseline from private config setup through artifact validation without printing private domains, TLS paths, or network-change commands.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next phase | `active-network-change` |
| next trial ready | `no` |
| packet state | `blocked_by_readiness` |
| needed-now gates | `baseline_summary_ready; network_change_command_present` |

## Ordered Stages

| stage | order | status | owner | action | command | stop condition |
| --- | --- | --- | --- | --- | --- | --- |
| 0-private-config | 1 | `blocked` | operator | Create and fill the ignored controlled-public origin config. | `bash harness/scripts/init-controlled-public-config.sh && $EDITOR harness/config/controlled-public-origin.env` | stop until needed-now gates are cleared |
| 1-preflight | 2 | `blocked` | operator | Run the final P0 baseline preflight wrapper before starting server/client artifacts. | `bash harness/scripts/final-p0-baseline-preflight.sh` | stop if any required gate remains missing |
| 2-origin-server | 3 | `blocked` | origin-host | Start the controlled public H3 origin server for the selected baseline trial. | `cd repro/quic-go-min-repro<br>RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 \<br>ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \<br>PUBLIC_ORIGIN_HOST=h3.example.com \<br>PUBLIC_ORIGIN_PORT=443 \<br>TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \<br>TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \<br>LISTEN_ADDR=0.0.0.0:443 \<br>TCP_ADDR=0.0.0.0:443 \<br>ALT_SVC='h3=":443"; ma=60' \<br>EXPECTED_REQUESTS=2 \<br>TIMEOUT=300s \<br>COMPLETION_GRACE=2s \<br>./scripts/run-controlled-public-h3-server.sh` | stop if baseline preflight is not ready |
| 3-browser-client | 4 | `blocked` | client-host | Run the final P0 Chrome baseline wrapper and collect/validate browser artifacts. | `bash harness/scripts/final-p0-baseline-run.sh` | stop if server/origin terminal is not running or wrapper postchecks fail |
| 4-post-trial-registration | 5 | `blocked` | operator | Validate artifacts, append the final handover row, and regenerate final-trial audit outputs. | `TRIAL_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 ARTIFACT_DIR=repro/quic-go-min-repro/artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 APPLY=1 bash harness/scripts/final-handover-register-trial.sh` | stop if raw artifact bundle or final-countable validation fails |

## Interpretation

- Run stage 0 and stage 1 first; do not start server/client artifact capture while needed-now gates remain.
- The origin-server command remains a public-template command; the client wrapper reads the private config locally.
- After a PASS baseline is registered, regenerate P0 status; the next blocker should move from baseline config to active path-change readiness.
