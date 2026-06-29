# iPhone USB Latent Failover Check

| field | value |
| --- | --- |
| date | `2026-06-29` |
| mode | `measure` |
| Wi-Fi device | `en0` |
| iPhone USB device | `en8` |
| ready | `yes` |
| ready at | `548` ms |
| classification | `latent_iphone_usb_failover_observed` |
| before default interface | `en0` |
| after default interface | `en8` |
| network-change exit | `0` |

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.
