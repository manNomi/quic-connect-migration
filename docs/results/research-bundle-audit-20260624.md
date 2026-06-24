# Research Bundle Audit

Generated: `2026-06-24`

## Summary

| check | value |
| --- | --- |
| publication bundle ok | `yes` |
| required files ok | `yes` |
| experiment trials | `35` |
| experiment status counts | `{'PASS': 18, 'PASS_NEGATIVE_CONTROL': 16, 'PASS_FEASIBILITY': 1}` |
| experiment ids unique | `yes` |
| matrix items | `53` |
| matrix ids unique | `yes` |
| paper tables current | `yes` |
| goal complete | `no` |

## Readiness

| check | value |
| --- | --- |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `no` |
| desktop handover ready | `no` |
| Android ready | `no` |
| AWS identity OK | `no` |
| disk available GiB | `2.44` |
| local artifact roots total | `908.3 MiB` |
| Chrome NetLog ready | `yes` |
| Safari WebDriver ready | `yes` |
| packet capture tooling ready | `yes` |

## Blockers

- desktop active secondary path is not ready
- Android device is not connected over ADB
- AWS identity is not available
- disk free space is below 5 GiB; large NetLog/pcap experiments should wait
- browser active network-change result is not done
- controlled-public network-change result is not done
