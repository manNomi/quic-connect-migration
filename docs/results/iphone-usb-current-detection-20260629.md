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
| classification | `iphone_usb_service_configured_hardware_absent` |
| before default interface | `en0` |
| after default interface | `en0` |
| network-change exit | `-` |

## iPhone USB Inventory

| field | before | after |
| --- | --- | --- |
| service configured | `yes` | `yes` |
| service device | `en8` | `en8` |
| hardware port present | `no` | `no` |
| hardware device | `-` | `-` |
| ifconfig listed | `no` | `no` |
| interface present | `no` | `no` |
| interface active | `no` | `no` |

## Next Actions

- Reconnect the USB-C cable and unlock the iPhone.
- Enable Personal Hotspot on the iPhone and keep the screen awake for the next check.
- Check macOS System Settings > Network and confirm the iPhone USB service is physically present, not only remembered as a saved service.
- Rerun this checker before running a browser handover trial.

## Claim Boundary

This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration.
