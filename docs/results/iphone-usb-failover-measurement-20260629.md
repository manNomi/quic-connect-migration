# iPhone USB Latent Failover Check

| field | value |
| --- | --- |
| date | `2026-06-29` |
| mode | `measure` |
| Wi-Fi device | `en0` |
| iPhone USB service | `iPhone USB` |
| iPhone USB device | `en8` |
| ready | `yes` |
| ready at | `1347` ms |
| classification | `latent_iphone_usb_failover_observed` |
| before default interface | `en0` |
| after default interface | `en8` |
| network-change exit | `0` |

## iPhone USB Inventory

| field | before | after |
| --- | --- | --- |
| service configured | `yes` | `yes` |
| service device | `en8` | `en8` |
| hardware port present | `yes` | `yes` |
| hardware device | `en8` | `en8` |
| ifconfig listed | `yes` | `yes` |
| interface present | `yes` | `yes` |
| interface active | `no` | `yes` |

## Next Actions

- Use ALLOW_LATENT_SECONDARY_PATH=1 and NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" for page-ready trials.
- Report the setup as delayed OS failover, not simultaneous active multipath.

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.
