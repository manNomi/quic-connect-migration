# Final Handover Next Trial Readiness

Generated: `2026-06-30`

## Summary

| field | value |
| --- | --- |
| ready | `no` |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `yes` |
| check local files | `no` |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next phase | `active-network-change` |
| next browser | `Chrome` |
| final completion | `3/6` |
| disk free GiB | `13.45` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| desktop path-change mode | `not-ready` |
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
| `latent_iphone_usb_candidate_ready` | `no` | `no` |
| `allow_latent_secondary_path` | `no` | `no` |
| `desktop_path_change_ready` | `no` | `yes` |
| `baseline_summary_ready` | `no` | `yes` |
| `network_change_command_present` | `no` | `yes` |
| `android_network_change_command_present` | `no` | `no` |

## Missing Required Gates

- baseline_summary_ready
- network_change_command_present
- desktop_path_change_ready

## iPhone USB Diagnostic

| field | value |
| --- | --- |
| classification | `iphone_usb_service_configured_hardware_absent` |
| ready | `no` |
| service | `iPhone USB` |
| device | `en8` |
| before default interface | `en0` |
| after default interface | `en0` |
| service configured | `yes` |
| hardware port present | `no` |
| ifconfig listed | `no` |

Next actions:

- Reconnect the USB-C cable and unlock the iPhone.
- Enable Personal Hotspot on the iPhone and keep the screen awake for the next check.
- Check macOS System Settings > Network and confirm the iPhone USB service is physically present, not only remembered as a saved service.
- Rerun this checker before running a browser handover trial.

## Next Trial Commands

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
