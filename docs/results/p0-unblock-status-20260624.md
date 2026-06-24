# P0 Unblock Status

Generated: `2026-06-24`

This tracker is public-safe. It compresses final protocol readiness into the gates that currently block the P0 controlled-public/browser handover path.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-h3-baseline-001` |
| next phase | `baseline` |
| total planned trials | `10` |
| blocked planned trials | `10` |
| final requirements complete | `0/6` |
| needed-now gates | `4` |

## Blocking Gates

| order | gate | status | blocked trials | blocks next | operator action | validation command |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `controlled_public_config_present` | `needed-now` | 10 | `yes` | Create the ignored controlled-public origin env file and fill non-secret baseline fields locally. | `python3 tools/check_controlled_public_config.py --require-baseline-ready` |
| 2 | `public_origin_host_configured` | `needed-now` | 10 | `yes` | Set the public origin host in the private controlled-public config. | `python3 tools/check_controlled_public_config.py --require-baseline-ready` |
| 3 | `public_origin_url_configured` | `needed-now` | 10 | `yes` | Set the public WebPKI URL and verify Alt-Svc/H3 readiness. | `python3 tools/check_public_origin_readiness.py --url "$PUBLIC_ORIGIN_URL" --require-h3-alt-svc --format markdown` |
| 4 | `tls_config_present` | `needed-now` | 10 | `yes` | Set TLS certificate and key paths on the private origin host/config. | `python3 tools/check_controlled_public_config.py --require-baseline-ready` |
| 5 | `baseline_summary_ready` | `needed-after-baseline` | 7 | `no` | Run and register the controlled-public Chrome application H3 baseline. | `python3 tools/check_controlled_public_baseline_unlock.py --require-unlocked` |
| 6 | `desktop_secondary_path_ready` | `needed-after-baseline` | 7 | `no` | Prepare a real active secondary non-loopback path for desktop browser trials. | `python3 tools/check_handover_readiness.py --format markdown` |
| 7 | `network_change_command_present` | `needed-after-baseline` | 7 | `no` | Provide an operator-approved active network-change command. | `python3 tools/check_controlled_public_config.py --require-active-ready` |

## Safe Handling

- `controlled_public_config_present`: Do not commit the private env file or real domain/certificate paths.
- `public_origin_host_configured`: Do not print the real host in tracked reports.
- `public_origin_url_configured`: Use redacted/public-safe summaries only.
- `tls_config_present`: Never commit private keys or local certificate paths.
- `baseline_summary_ready`: Register only validated summaries with raw artifact bundle references kept local/ignored.
- `desktop_secondary_path_ready`: Do not infer path change from server tuple evidence alone.
- `network_change_command_present`: Do not commit machine-specific interface commands.

## Interpretation

- The next concrete P0 step is to clear all `needed-now` gates for `controlled-public-chrome-h3-baseline-001`.
- Active network-change gates remain after-baseline work until the controlled public application H3 baseline is registered.
- This tracker does not create result evidence; it prevents premature execution and premature browser CM claims.
