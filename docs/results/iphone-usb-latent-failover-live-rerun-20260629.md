# iPhone USB Latent Failover Check

| field | value |
| --- | --- |
| date | `2026-06-29` |
| mode | `measure` |
| Wi-Fi device | `en0` |
| iPhone USB device | `en8` |
| ready | `yes` |
| ready at | `1321` ms |
| classification | `latent_iphone_usb_failover_observed` |
| before default interface | `en0` |
| after default interface | `en8` |
| network-change exit | `0` |

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.

## Event Summary

The rerun started with Wi-Fi `en0` as the default interface. After the Wi-Fi-off command, macOS briefly had no default interface in the captured snapshots, then selected iPhone USB `en8` with a usable IPv4 address at `1321` ms. Wi-Fi restoration exited successfully after the measurement.
