# iPhone USB Latent Failover Mode

Date: `2026-06-29`

## Why This Matters

The Mac+iPhone setup did not expose Wi-Fi and iPhone USB tethering as two simultaneously active usable IPv4 paths. With Wi-Fi enabled, `iPhone USB` was present as `en8` but inactive. When Wi-Fi was disabled, macOS activated `en8` and moved the default route to the iPhone cellular path.

This means the desktop handover setup should be modeled as **latent failover**, not as a strict **active-secondary-path** setup.

## Measurement

Measured with `tools/check_iphone_usb_latent_failover.py --measure`.

| field | value |
| --- | --- |
| classification | `latent_iphone_usb_failover_observed` |
| Wi-Fi device | `en0` |
| iPhone USB device | `en8` |
| before default interface | `en0` |
| before iPhone USB state | `present=true, active=false, usable_ipv4=0` |
| network-change command exit | `0` |
| ready at | `575 ms` |
| after default interface | `en8` |
| after iPhone USB state | `present=true, active=true, usable_ipv4=1` |

Event timing from the machine-readable artifact:

| t_ms | Wi-Fi power | default interface | iPhone USB state |
| ---: | --- | --- | --- |
| 28 | `On` | `en0` | `present, inactive, no IPv4` |
| 259 | `Off` | `en0` | `present, inactive, no IPv4` |
| 575 | `Off` | `en8` | `present, active, usable IPv4` |
| 605 | `Off` | `en8` | `present, active, usable IPv4` |

Raw artifact: `data/iphone-usb-latent-failover-20260629.json`

## Candidate Detection

After restoring Wi-Fi, the command-candidate scanner reported:

| field | value |
| --- | --- |
| active IPv4 interfaces | `en0` |
| secondary path ready | `no` |
| latent iPhone USB candidate ready | `yes` |
| ready candidate | `macos_wifi_to_iphone_usb_latent_failover` |

Candidate artifact: `docs/results/active-path-change-candidates-20260629.md`

## Interpretation

This is a valid real client path-change trigger for browser handover experiments because the active route changes from Wi-Fi to iPhone cellular/USB after the trigger.

It is **not** evidence that the browser performed single-connection QUIC Connection Migration. Final trial interpretation still needs the normal evidence chain:

- client before/after path snapshots
- server request tuple evidence
- server qlog path validation evidence
- Chrome NetLog QUIC session and path events
- workload completion or failure result

## Protocol Impact

The controlled public desktop trial gate now needs two explicit modes:

| mode | meaning | claim boundary |
| --- | --- | --- |
| `active-secondary-path` | Wi-Fi and secondary path are active before the trigger | Can test active migration with an already available alternate path |
| `latent-iphone-usb-failover` | iPhone USB is inactive while Wi-Fi is active, then activates after Wi-Fi loss | Tests delayed OS failover plus browser recovery/migration behavior |

The second mode is closer to a real user failure case, but it includes an OS path-activation delay. Therefore it should be reported as Wi-Fi-loss-to-cellular-failover behavior, not as pure simultaneous-path QUIC migration.
