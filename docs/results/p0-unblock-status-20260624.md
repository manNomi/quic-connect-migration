# P0 Unblock Status

Generated: `2026-07-01`

This tracker is public-safe. It compresses final protocol readiness into the gates that currently block the P0 controlled-public/browser handover path.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next phase | `active-network-change` |
| total planned trials | `10` |
| blocked planned trials | `7` |
| final requirements complete | `3/6` |
| needed-now gates | `3` |
| local next-trial overlay | `not-used` |
| local next-trial ready | `-` |
| local missing required gates | - |

## Blocking Gates

| order | gate | status | blocked trials | blocks next | operator action | validation command |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `baseline_summary_ready` | `needed-now` | 7 | `yes` | Run and register the controlled-public Chrome application H3 baseline. | `python3 tools/check_controlled_public_baseline_unlock.py --require-unlocked` |
| 2 | `desktop_secondary_path_ready` | `needed-now` | 7 | `yes` | Prepare a real active secondary non-loopback path for desktop browser trials. | `python3 tools/check_handover_readiness.py --format markdown` |
| 3 | `network_change_command_present` | `needed-now` | 7 | `yes` | Provide an operator-approved active network-change command. | `python3 tools/check_controlled_public_config.py --require-active-ready` |

## Safe Handling

- `baseline_summary_ready`: Register only validated summaries with raw artifact bundle references kept local/ignored.
- `desktop_secondary_path_ready`: Do not infer path change from server tuple evidence alone.
- `network_change_command_present`: Do not commit machine-specific interface commands.

## Interpretation

- The next concrete final-handover step is to clear all `needed-now` gates for the displayed next trial.
- When the local overlay is `applied`, `blocks next` reflects the ignored local config/readiness state rather than only the tracked public matrix.
- Active network-change gates remain after-baseline work until the controlled public application H3 baseline is registered.
- This tracker does not create result evidence; it prevents premature execution and premature browser CM claims.
