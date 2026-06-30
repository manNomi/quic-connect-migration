# Research Bundle Audit

Generated: `2026-06-30`

## Summary

| check | value |
| --- | --- |
| publication bundle ok | `yes` |
| required files ok | `yes` |
| experiment trials | `99` |
| experiment status counts | `{'PASS': 33, 'PASS_NEGATIVE_CONTROL': 60, 'PASS_FEASIBILITY': 6}` |
| experiment ids unique | `yes` |
| matrix items | `159` |
| matrix ids unique | `yes` |
| paper tables current | `yes` |
| final browser handover trials | `3/6` |
| goal complete | `no` |

## Readiness

| check | value |
| --- | --- |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `no` |
| desktop handover ready | `no` |
| Android ready | `no` |
| AWS identity OK | `no` |
| disk available GiB | `13.21` |
| local artifact roots total | `36.3 GiB` |
| Chrome NetLog ready | `yes` |
| Safari WebDriver ready | `yes` |
| packet capture tooling ready | `yes` |

## Final Browser Handover Trials

| check | value |
| --- | --- |
| complete | `no` |
| requirements complete | `3/6` |

Incomplete final trial requirements:

- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- p1-safari-or-android-feasibility: 0/1

## Blockers

- desktop active secondary path is not ready
- Android device is not connected over ADB
- AWS identity is not available
- final browser handover trial protocol is not complete
