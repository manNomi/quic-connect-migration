# Controlled Public Config Worksheet

Generated: `2026-07-01`

This worksheet is public-safe. It reports presence, validity, ownership, and next actions without printing actual domains, TLS paths, private keys, or network-change commands.

## Summary

| field | value |
| --- | --- |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `yes` |
| check local files | `no` |
| baseline config ready | `yes` |
| active network-change config ready | `no` |
| Android network-change config ready | `no` |
| next step | `run_baseline_then_fill_active_config` |

## Missing By Stage

| stage | keys |
| --- | --- |
| baseline | `-` |
| active | `NETWORK_CHANGE_CMD` |
| android | `ANDROID_NETWORK_CHANGE_CMD` |

## Fields

| stage | key | owner | privacy | expected shape | valid | next action |
| --- | --- | --- | --- | --- | --- | --- |
| `baseline` | `PUBLIC_ORIGIN_HOST` | origin/client | private lab domain | DNS hostname controlled by the researcher | `yes` | ready |
| `baseline` | `PUBLIC_ORIGIN_PORT` | origin/client | safe if generic | integer TCP/UDP port, usually 443 | `yes` | ready |
| `baseline` | `PUBLIC_ORIGIN_URL` | client | private lab URL | https URL whose host equals PUBLIC_ORIGIN_HOST and whose port equals PUBLIC_ORIGIN_PORT | `yes` | ready |
| `baseline` | `TLS_CERT_FILE` | origin host | private filesystem path | absolute path to WebPKI fullchain certificate | `yes` | ready |
| `baseline` | `TLS_KEY_FILE` | origin host | secret filesystem path | absolute path to private key readable only on origin host | `yes` | ready |
| `baseline` | `LISTEN_ADDR` | origin host | safe if generic | IP:port listener address, usually 0.0.0.0:443 | `yes` | ready |
| `baseline` | `TCP_ADDR` | origin host | safe if generic | IP:port listener address, usually 0.0.0.0:443 | `yes` | ready |
| `baseline` | `ALT_SVC` | origin host | safe if generic | Alt-Svc value containing h3 and a port, e.g. h3=":443"; ma=60 | `yes` | ready |
| `baseline` | `CHROME_BIN` | client | local filesystem path | absolute path to Chrome executable | `yes` | ready |
| `active` | `PUBLIC_ORIGIN_NETWORK_CHANGE_URL` | client | private lab URL | long-running https workload URL whose host equals PUBLIC_ORIGIN_HOST and whose port equals PUBLIC_ORIGIN_PORT | `yes` | ready |
| `active` | `CONTROLLED_PUBLIC_BASELINE_SUMMARY` | client | local artifact path | path to baseline summary JSON with status=PASS | `yes` | ready |
| `active` | `NETWORK_CHANGE_AFTER_SECONDS` | client | safe if generic | integer delay before running the explicit path-change command | `yes` | ready |
| `active` | `NETWORK_CHANGE_CMD` | client | dangerous local command | explicit command approved by the operator for this machine/network | `no` | add NETWORK_CHANGE_CMD to the local env file |
| `android` | `ANDROID_NETWORK_CHANGE_CMD` | client/android | dangerous local command | explicit ADB or host command approved by the operator | `no` | add ANDROID_NETWORK_CHANGE_CMD to the local env file |

## Run Order

1. Run `bash harness/scripts/init-controlled-public-config.sh` to create the ignored local config path without overwriting an existing file.
2. Fill baseline fields on the public origin host and client machine.
3. Run `python3 tools/check_controlled_public_config.py --require-baseline-ready`.
4. Run the controlled-public H3 baseline and keep the `status=PASS` summary.
5. Fill active network-change fields only after choosing a real secondary path and an explicit command.
6. Run final handover trials only after readiness and artifact bundle gates pass.
