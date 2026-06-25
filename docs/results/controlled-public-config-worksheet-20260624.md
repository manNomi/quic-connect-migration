# Controlled Public Config Worksheet

Generated: `2026-06-25`

This worksheet is public-safe. It reports presence, validity, ownership, and next actions without printing actual domains, TLS paths, private keys, or network-change commands.

## Summary

| field | value |
| --- | --- |
| config path | `harness/config/controlled-public-origin.env` |
| config exists | `no` |
| check local files | `no` |
| baseline config ready | `no` |
| active network-change config ready | `no` |
| Android network-change config ready | `no` |
| next step | `fill_baseline_config` |

## Missing By Stage

| stage | keys |
| --- | --- |
| baseline | `PUBLIC_ORIGIN_HOST, PUBLIC_ORIGIN_PORT, PUBLIC_ORIGIN_URL, TLS_CERT_FILE, TLS_KEY_FILE, LISTEN_ADDR, TCP_ADDR, ALT_SVC, CHROME_BIN` |
| active | `PUBLIC_ORIGIN_NETWORK_CHANGE_URL, CONTROLLED_PUBLIC_BASELINE_SUMMARY, NETWORK_CHANGE_AFTER_SECONDS, NETWORK_CHANGE_CMD` |
| android | `ANDROID_NETWORK_CHANGE_CMD` |

## Fields

| stage | key | owner | privacy | expected shape | valid | next action |
| --- | --- | --- | --- | --- | --- | --- |
| `baseline` | `PUBLIC_ORIGIN_HOST` | origin/client | private lab domain | DNS hostname controlled by the researcher | `no` | add PUBLIC_ORIGIN_HOST to the local env file |
| `baseline` | `PUBLIC_ORIGIN_PORT` | origin/client | safe if generic | integer TCP/UDP port, usually 443 | `no` | add PUBLIC_ORIGIN_PORT to the local env file |
| `baseline` | `PUBLIC_ORIGIN_URL` | client | private lab URL | https URL whose host equals PUBLIC_ORIGIN_HOST and whose port equals PUBLIC_ORIGIN_PORT | `no` | add PUBLIC_ORIGIN_URL to the local env file |
| `baseline` | `TLS_CERT_FILE` | origin host | private filesystem path | absolute path to WebPKI fullchain certificate | `no` | add TLS_CERT_FILE to the local env file |
| `baseline` | `TLS_KEY_FILE` | origin host | secret filesystem path | absolute path to private key readable only on origin host | `no` | add TLS_KEY_FILE to the local env file |
| `baseline` | `LISTEN_ADDR` | origin host | safe if generic | IP:port listener address, usually 0.0.0.0:443 | `no` | add LISTEN_ADDR to the local env file |
| `baseline` | `TCP_ADDR` | origin host | safe if generic | IP:port listener address, usually 0.0.0.0:443 | `no` | add TCP_ADDR to the local env file |
| `baseline` | `ALT_SVC` | origin host | safe if generic | Alt-Svc value containing h3 and a port, e.g. h3=":443"; ma=60 | `no` | add ALT_SVC to the local env file |
| `baseline` | `CHROME_BIN` | client | local filesystem path | absolute path to Chrome executable | `no` | add CHROME_BIN to the local env file |
| `active` | `PUBLIC_ORIGIN_NETWORK_CHANGE_URL` | client | private lab URL | long-running https workload URL whose host equals PUBLIC_ORIGIN_HOST and whose port equals PUBLIC_ORIGIN_PORT | `no` | add PUBLIC_ORIGIN_NETWORK_CHANGE_URL to the local env file |
| `active` | `CONTROLLED_PUBLIC_BASELINE_SUMMARY` | client | local artifact path | path to baseline summary JSON with status=PASS | `no` | add CONTROLLED_PUBLIC_BASELINE_SUMMARY to the local env file |
| `active` | `NETWORK_CHANGE_AFTER_SECONDS` | client | safe if generic | integer delay before running the explicit path-change command | `no` | add NETWORK_CHANGE_AFTER_SECONDS to the local env file |
| `active` | `NETWORK_CHANGE_CMD` | client | dangerous local command | explicit command approved by the operator for this machine/network | `no` | add NETWORK_CHANGE_CMD to the local env file |
| `android` | `ANDROID_NETWORK_CHANGE_CMD` | client/android | dangerous local command | explicit ADB or host command approved by the operator | `no` | add ANDROID_NETWORK_CHANGE_CMD to the local env file |

## Run Order

1. Run `bash harness/scripts/init-controlled-public-config.sh` to create the ignored local config path without overwriting an existing file.
2. Fill baseline fields on the public origin host and client machine.
3. Run `python3 tools/check_controlled_public_config.py --require-baseline-ready`.
4. Run the controlled-public H3 baseline and keep the `status=PASS` summary.
5. Fill active network-change fields only after choosing a real secondary path and an explicit command.
6. Run final handover trials only after readiness and artifact bundle gates pass.
