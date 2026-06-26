# iPhone USB Boundary And Active Short Trial

작성일: 2026-06-26

## 목적

이 실험 묶음은 macOS + Chrome + iPhone USB tethering 조건에서 HTTP/3 no-change baseline의 안정 구간을 먼저 찾고, 그 안정 구간 위에서 active network-change를 다시 시도하기 위해 수행했다. 이전 long active trial은 application failure가 있었지만, baseline 자체가 불안정하다는 반론이 남아 있었다. 그래서 같은 workload가 no-change에서는 완료되는지 먼저 확인했다.

## No-Change Boundary 결과

모든 no-change boundary trial은 workload 시작 전에 Wi-Fi를 끄고 default/target route가 `en8`이 된 것을 확인한 뒤 실행했다.

| trial | route | workload | app result | protocol evidence |
| --- | --- | --- | --- | --- |
| `boundary5000-16kb` | `en8` / `en8` | 5s, 16KB, 5 chunks | `downlinkComplete=true`, `16576 bytes`, `5326ms` | `chosen_alpn=2`, `http3_frame=18` |
| `boundary8000-32kb` | `en8` / `en8` | 8s, 32KB, 8 chunks | `downlinkComplete=true`, `32960 bytes`, `7045ms` | `chosen_alpn=2`, `http3_frame=20` |
| `boundary12000-64kb` | `en8` / `en8` | 12s, 64KB, 12 chunks | `downlinkComplete=true`, `65729 bytes`, `12126ms` | `chosen_alpn=2`, `http3_frame=25` |

공통 관찰:

- pre-cutover default route: `en8`
- pre-cutover target route: `en8`
- active IPv4 interface: `en8`, `172.20.10.8`
- public IP probe: `106.101.2.80`
- qlog PATH_CHALLENGE/PATH_RESPONSE: 0/0

## Active Short Network-Change 결과

`boundary8000-32kb`는 no-change에서 성공한 workload였기 때문에 같은 조건으로 active path-change를 걸었다.

| 항목 | 결과 |
| --- | --- |
| workload | 8s, 32KB, 8 chunks |
| trigger | workload 시작 후 2초에 `networksetup -setairportpower en0 off` |
| route change | `en0` -> `en8` |
| target H3 remote addr count | 1 |
| qlog PATH_CHALLENGE/PATH_RESPONSE | 0/0 |
| classifier | `PASS_NEGATIVE_CONTROL / application_task_incomplete_without_quic_path_validation` |

| trial | immediate/eventual path | app dataset | qlog path validation | target H3 remote addr count |
| --- | --- | --- | --- | ---: |
| `network-change-001` | `client_active_path_changed` / `client_active_path_changed` | `downlinkBytes=4120`, no complete/error | 0/0 | 1 |
| `network-change-002` | `client_active_path_changed` / `client_active_path_changed` | `downlinkBytes=8242`, no complete/error | 0/0 | 1 |
| `network-change-003` | `client_active_path_changed` / `client_active_path_changed` | `downlinkBytes=8242`, no complete/error | 0/0 | 1 |

## 해석

이 결과는 이전보다 더 강한 negative-control이다. 같은 `8s/32KB` workload는 iPhone USB pre-cutover no-change에서 완료됐지만, active `en0 -> en8` path-change 조건에서는 3/3 반복 모두 완료되지 않았다. 따라서 이번 active 실패는 단순히 workload가 iPhone USB에서 불안정해서 생긴 결과라고 보기 어렵다.

다만 이것도 Chrome connection migration positive/negative를 단정하는 최종 증거는 아니다. 서버 qlog에서 PATH_CHALLENGE/PATH_RESPONSE가 없었고 target H3 remote addr count도 1이라, 관찰된 것은 "active route change가 발생했지만 Chrome의 해당 in-flight H3 downlink task가 QUIC path validation으로 이어지지 않았고 application completion도 없었다"는 것이다.

## 논문상 사용 가능한 주장

- browser CM 검증은 no-change baseline stability를 먼저 확인해야 한다.
- stable no-change workload라도 desktop tethering active path-change에서 application continuity가 보장되지 않을 수 있다.
- 이 환경에서는 route change와 QUIC path validation/application completion 사이에 큰 관측 gap이 있다.
- 따라서 "QUIC 구현체가 CM을 지원한다"와 "브라우저 환경에서 사용자 작업이 이어진다"는 별개의 평가 축이다.

## 다음 단계

1. trigger 시점을 2초, 4초, 6초로 바꿔 application incompletion이 trigger timing에 민감한지 확인한다.
2. 같은 stable workload에 heartbeat 또는 retry를 추가해 application-level recovery가 continuity를 회복하는지 별도 negative/control row로 측정한다.
3. Android Chrome 또는 Safari/iOS에서 동일한 stable workload를 사용해 OS-native handover 가능성을 비교한다.
