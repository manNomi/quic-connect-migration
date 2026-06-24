# Controlled Public Config Check

Generated: `2026-06-24`

## Summary

| field | value |
| --- | --- |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `no` |
| check local files | `no` |
| baseline config ready | `no` |
| active network-change config ready | `no` |
| Android network-change config ready | `no` |
| public safe | `yes` |

## Key Checks

| key | present | placeholder | valid | detail |
| --- | --- | --- | --- | --- |
| `PUBLIC_ORIGIN_HOST` | `no` | `yes` | `no` | `missing` |
| `PUBLIC_ORIGIN_PORT` | `no` | `yes` | `no` | `missing` |
| `PUBLIC_ORIGIN_URL` | `no` | `yes` | `no` | `missing` |
| `TLS_CERT_FILE` | `no` | `yes` | `no` | `missing` |
| `TLS_KEY_FILE` | `no` | `yes` | `no` | `missing` |
| `LISTEN_ADDR` | `no` | `yes` | `no` | `missing` |
| `TCP_ADDR` | `no` | `yes` | `no` | `missing` |
| `ALT_SVC` | `no` | `yes` | `no` | `missing` |
| `CHROME_BIN` | `no` | `yes` | `no` | `missing` |
| `PUBLIC_ORIGIN_NETWORK_CHANGE_URL` | `no` | `yes` | `no` | `missing` |
| `CONTROLLED_PUBLIC_BASELINE_SUMMARY` | `no` | `yes` | `no` | `missing` |
| `NETWORK_CHANGE_AFTER_SECONDS` | `no` | `yes` | `no` | `missing` |
| `NETWORK_CHANGE_CMD` | `no` | `yes` | `no` | `missing` |
| `ANDROID_NETWORK_CHANGE_CMD` | `no` | `yes` | `no` | `missing` |

## Blockers

- controlled public config file is missing
- baseline config key not ready: PUBLIC_ORIGIN_HOST (missing)
- baseline config key not ready: PUBLIC_ORIGIN_PORT (missing)
- baseline config key not ready: PUBLIC_ORIGIN_URL (missing)
- baseline config key not ready: TLS_CERT_FILE (missing)
- baseline config key not ready: TLS_KEY_FILE (missing)
- baseline config key not ready: LISTEN_ADDR (missing)
- baseline config key not ready: TCP_ADDR (missing)
- baseline config key not ready: ALT_SVC (missing)
- baseline config key not ready: CHROME_BIN (missing)
- active network-change config key not ready: PUBLIC_ORIGIN_NETWORK_CHANGE_URL (missing)
- active network-change config key not ready: CONTROLLED_PUBLIC_BASELINE_SUMMARY (missing)
- active network-change config key not ready: NETWORK_CHANGE_AFTER_SECONDS (missing)
- active network-change config key not ready: NETWORK_CHANGE_CMD (missing)

This report intentionally does not print actual domain names, certificate paths, private key paths, or network-change commands.
