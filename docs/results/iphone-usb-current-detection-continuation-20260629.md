# iPhone USB Latent Failover Check

| field | value |
| --- | --- |
| date | `2026-06-29` |
| mode | `snapshot` |
| Wi-Fi device | `en0` |
| iPhone USB service | `iPhone USB` |
| iPhone USB device | `en8` |
| ready | `no` |
| ready at | `-` ms |
| classification | `iphone_usb_latent_candidate_unmeasured` |
| before default interface | `en0` |
| after default interface | `en0` |
| network-change exit | `-` |

## iPhone USB Inventory

| field | before | after |
| --- | --- | --- |
| service configured | `yes` | `yes` |
| service device | `en8` | `en8` |
| hardware port present | `yes` | `yes` |
| hardware device | `en8` | `en8` |
| ifconfig listed | `yes` | `yes` |
| interface present | `yes` | `yes` |
| interface active | `no` | `no` |

## Next Actions

- Run with --measure --restore-wifi to confirm delayed Wi-Fi-loss-to-iPhone-USB failover timing.
- Use the measured ready_at_ms as the path-change trigger preflight evidence.

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.
