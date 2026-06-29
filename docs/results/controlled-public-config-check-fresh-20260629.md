# Controlled Public Config Check

Generated: `2026-06-29`

## Summary

| field | value |
| --- | --- |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `yes` |
| check local files | `no` |
| baseline config ready | `yes` |
| active network-change config ready | `no` |
| Android network-change config ready | `no` |
| public safe | `yes` |

## Key Checks

| key | present | placeholder | valid | detail |
| --- | --- | --- | --- | --- |
| `PUBLIC_ORIGIN_HOST` | `yes` | `no` | `yes` | `valid_host` |
| `PUBLIC_ORIGIN_PORT` | `yes` | `no` | `yes` | `valid_port` |
| `PUBLIC_ORIGIN_URL` | `yes` | `no` | `yes` | `valid_https_url` |
| `TLS_CERT_FILE` | `yes` | `no` | `yes` | `present` |
| `TLS_KEY_FILE` | `yes` | `no` | `yes` | `present` |
| `LISTEN_ADDR` | `yes` | `no` | `yes` | `valid_addr_port` |
| `TCP_ADDR` | `yes` | `no` | `yes` | `valid_addr_port` |
| `ALT_SVC` | `yes` | `no` | `yes` | `valid_h3_alt_svc` |
| `CHROME_BIN` | `yes` | `no` | `yes` | `path_exists` |
| `PUBLIC_ORIGIN_NETWORK_CHANGE_URL` | `yes` | `no` | `yes` | `valid_https_url` |
| `CONTROLLED_PUBLIC_BASELINE_SUMMARY` | `yes` | `no` | `yes` | `present` |
| `NETWORK_CHANGE_AFTER_SECONDS` | `yes` | `no` | `yes` | `valid_non_negative_integer` |
| `NETWORK_CHANGE_CMD` | `no` | `yes` | `no` | `missing` |
| `ANDROID_NETWORK_CHANGE_CMD` | `no` | `yes` | `no` | `missing` |

## Blockers

- active network-change config key not ready: NETWORK_CHANGE_CMD (missing)

This report intentionally does not print actual domain names, certificate paths, private key paths, or network-change commands.
