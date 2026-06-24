# Final Handover Next Trial Readiness

Generated: `2026-06-24`

## Summary

| field | value |
| --- | --- |
| ready | `no` |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `no` |
| check local files | `no` |
| next trial | `controlled-public-chrome-h3-baseline-001` |
| next phase | `baseline` |
| next browser | `Chrome` |
| final completion | `0/6` |
| disk free GiB | `47.91` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| public origin URL | `-` |

## Required Gates

| gate | value | required |
| --- | --- | --- |
| `next_trial_selected` | `yes` | `yes` |
| `controlled_public_config_present` | `no` | `yes` |
| `public_origin_host_configured` | `no` | `yes` |
| `public_origin_url_configured` | `no` | `yes` |
| `tls_config_present` | `no` | `yes` |
| `tls_cert_file_exists` | `no` | `no` |
| `tls_key_file_exists` | `no` | `no` |
| `disk_ready` | `yes` | `yes` |
| `chrome_ready` | `yes` | `yes` |
| `safari_webdriver_ready` | `yes` | `no` |
| `android_adb_ready` | `no` | `no` |
| `desktop_secondary_path_ready` | `no` | `no` |
| `baseline_summary_ready` | `no` | `no` |
| `network_change_command_present` | `no` | `no` |
| `android_network_change_command_present` | `no` | `no` |

## Missing Required Gates

- controlled_public_config_present
- public_origin_host_configured
- public_origin_url_configured
- tls_config_present

## Next Trial Commands

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
