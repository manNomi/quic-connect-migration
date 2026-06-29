# iPhone USB Latent Failover Check

| field | value |
| --- | --- |
| date | `2026-06-29` |
| mode | `snapshot` |
| Wi-Fi device | `en0` |
| iPhone USB device | `en8` |
| ready | `no` |
| ready at | `-` ms |
| classification | `iphone_usb_latent_candidate_unmeasured` |
| before default interface | `en0` |
| after default interface | `en0` |
| network-change exit | `-` |

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.
