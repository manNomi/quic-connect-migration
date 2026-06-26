# Active Path-Change Command Candidates

Generated: `2026-06-26`

This report is read-only. It does not execute network-change commands.

## Summary

| field | value |
| --- | --- |
| active IPv4 interfaces | `en0` |
| default interface | `en0` |
| secondary path ready | `no` |
| ready candidates | `-` |
| commands included | `no` |

## Candidates

| candidate | ready | reason | command form | restore form |
| --- | --- | --- | --- | --- |
| `macos_wifi_power_cutover` | `no` | blocked: no active secondary non-loopback IPv4 path was detected | `networksetup -setairportpower <wifi-device> off` | `networksetup -setairportpower <wifi-device> on` |
| `macos_service_order_cutover` | `no` | blocked: no active secondary service was detected | `networksetup -ordernetworkservices <secondary-service> <primary-service> <remaining-services...>` | `networksetup -ordernetworkservices <primary-service> <secondary-service> <remaining-services...>` |
| `android_wifi_to_cellular_cutover` | `no` | blocked: no ADB device is connected | `adb shell svc wifi disable` | `adb shell svc wifi enable` |

## Claim Boundary

A candidate command is not migration evidence; count a trial only after before/after client path snapshots and server/qlog/NetLog artifacts validate it.
