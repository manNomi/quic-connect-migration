# Final Handover Next Trial Readiness

Generated: `2026-06-25`

## Summary

| field | value |
| --- | --- |
| ready | `yes` |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `yes` |
| check local files | `no` |
| next trial | `controlled-public-chrome-downlink-heartbeat-nochange-001` |
| next phase | `no-change-baseline` |
| next browser | `Chrome` |
| final completion | `2/6` |
| disk free GiB | `9.68` |
| active IPv4 interfaces | `en0(192.168.32.190)` |
| public origin URL | `<configured>` |

## Required Gates

| gate | value | required |
| --- | --- | --- |
| `next_trial_selected` | `yes` | `yes` |
| `controlled_public_config_present` | `yes` | `yes` |
| `public_origin_host_configured` | `yes` | `yes` |
| `public_origin_url_configured` | `yes` | `yes` |
| `tls_config_present` | `yes` | `yes` |
| `tls_cert_file_exists` | `no` | `no` |
| `tls_key_file_exists` | `no` | `no` |
| `disk_ready` | `yes` | `yes` |
| `chrome_ready` | `yes` | `yes` |
| `safari_webdriver_ready` | `yes` | `no` |
| `android_adb_ready` | `no` | `no` |
| `desktop_secondary_path_ready` | `no` | `no` |
| `baseline_summary_ready` | `yes` | `no` |
| `network_change_command_present` | `no` | `no` |
| `android_network_change_command_present` | `no` | `no` |

## Missing Required Gates

- -

## Next Trial Commands

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
