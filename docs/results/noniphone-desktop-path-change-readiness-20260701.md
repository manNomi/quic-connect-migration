# non-iPhone Desktop Path-Change Readiness

Generated: `2026-06-30`

This packet is public-safe and read-only. It does not execute network-change commands, and it excludes iPhone-based latent failover candidates.

## Summary

| field | value |
| --- | --- |
| active IPv4 interfaces | `en0` |
| default interface | `en0` |
| non-iPhone secondary interfaces | `-` |
| non-iPhone desktop path ready | `no` |
| ready candidates | `-` |
| commands included | `no` |

## Candidate Rows

| candidate | ready | reason | command template | restore template |
| --- | --- | --- | --- | --- |
| `macos_wifi_power_cutover` | `no` | blocked: no active secondary non-loopback IPv4 path was detected | `networksetup -setairportpower <wifi-device> off` | `networksetup -setairportpower <wifi-device> on` |
| `macos_service_order_cutover` | `no` | blocked: no active secondary service was detected | `networksetup -ordernetworkservices <secondary-service> <primary-service> <remaining-services...>` | `networksetup -ordernetworkservices <primary-service> <secondary-service> <remaining-services...>` |

## Excluded Candidates

| candidate | reason |
| --- | --- |
| `macos_wifi_to_iphone_usb_latent_failover` | iPhone-based or non-desktop path-change candidate |
| `android_wifi_to_cellular_cutover` | iPhone-based or non-desktop path-change candidate |

## Preconditions To Open This Gate

1. Connect or enable a non-iPhone secondary path such as Ethernet, USB LAN, Thunderbolt Ethernet, or another non-iPhone routed interface.
2. Confirm at least two active non-loopback IPv4 interfaces before setting `NETWORK_CHANGE_CMD`.
3. Capture before/after route snapshots with `tools/capture_network_path_snapshot.py` against the controlled public H3 origin.
4. Accept an active row only if `tools/compare_network_path_snapshots.py` reports `client_active_path_changed`.
5. Keep concrete interface names, commands, hostnames, qlogs, NetLogs, pcaps, keylogs, and private config out of committed files.

## Blockers

- only one active non-loopback IPv4 interface is currently detected
- no active non-iPhone secondary desktop interface is currently detected
- NETWORK_CHANGE_CMD must remain operator-provided and uncommitted

## Claim Boundary

This is readiness evidence only. It excludes iPhone latent failover and does not prove browser Connection Migration until a controlled public trial records client path change, server tuple change, qlog path validation, Chrome session continuity, and application completion.
