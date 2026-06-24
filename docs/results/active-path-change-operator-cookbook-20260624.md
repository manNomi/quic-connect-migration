# Active Path-Change Operator Cookbook

작성일: 2026-06-24

## 목적

final browser handover 실험의 두 번째 blocker는 실제 active path-change다. 이 문서는 `NETWORK_CHANGE_CMD` 또는 `ANDROID_NETWORK_CHANGE_CMD`를 임의로 자동 생성하지 않는다. 대신 operator가 안전하게 후보를 만들고, 실행 전후에 path 변화가 실제로 생겼는지 검증하는 절차를 고정한다.

핵심 원칙:

- active secondary path가 준비되기 전에는 Wi-Fi를 끄지 않는다.
- command exit code가 0이어도 handover 성공으로 보지 않는다.
- server tuple 변화만으로 CM을 주장하지 않는다.
- `client-path-change-summary.json`에서 `client_active_path_changed`가 나와야 active trial로 인정한다.

## 1. Read-only 진단

먼저 현재 장비가 두 개 이상의 active non-loopback IPv4 path를 갖는지 확인한다.

```bash
python3 tools/check_handover_readiness.py --format markdown
python3 tools/capture_network_path_snapshot.py \
  --url https://www.google.com/generate_204 \
  --output /tmp/quic-cm-path-before.json
```

성공 기준:

| 항목 | 기준 |
| --- | --- |
| active IPv4 interfaces | 최소 2개 |
| default route | primary와 secondary 전환 가능 |
| target route | controlled public origin으로 가는 route가 전환 가능 |
| Android option | ADB device가 있고 Wi-Fi/cellular가 모두 사용 가능 |

현재 repository audit 기준으로는 active IPv4가 `en0` 하나라 desktop active path-change는 아직 ready가 아니다.

## 2. macOS desktop 후보

macOS desktop에서는 operator가 직접 장비 상태를 보고 command를 고른다. 아래는 template이며 그대로 commit하거나 자동 실행하지 않는다.

### 2.1 Service inventory

```bash
networksetup -listallhardwareports
networksetup -listnetworkserviceorder
route get <public-origin-host>
```

### 2.2 Preferred setup

권장 구성:

```text
Wi-Fi: primary path
iPhone USB or Ethernet: active secondary path
controlled public origin: public WebPKI H3 server
```

### 2.3 Trigger templates

아래 command는 예시 template이다. 실제 service name은 장비마다 다르다.

```bash
# primary Wi-Fi를 끄고 active secondary path로 보내는 후보
NETWORK_CHANGE_CMD='networksetup -setairportpower Wi-Fi off'

# 실험 후 복구 command 후보
NETWORK_RESTORE_CMD='networksetup -setairportpower Wi-Fi on'
```

대체 후보:

```bash
# service priority를 바꾸는 방식. 실제 service names 확인 필수.
NETWORK_CHANGE_CMD='networksetup -ordernetworkservices "iPhone USB" "Wi-Fi"'
NETWORK_RESTORE_CMD='networksetup -ordernetworkservices "Wi-Fi" "iPhone USB"'
```

주의:

- SSH나 원격 접속 중이라면 primary network를 끄면 작업 세션이 끊길 수 있다.
- secondary path가 실제 internet reachability를 갖는지 먼저 확인한다.
- command는 `harness/config/controlled-public-origin.env`에만 넣고 commit하지 않는다.

## 3. Android 후보

Android Chrome P1 feasibility는 desktop보다 Wi-Fi/LTE handover 의미가 명확할 수 있다. 다만 carrier/device 상태에 의존한다.

Read-only checks:

```bash
adb devices
python3 tools/check_handover_readiness.py --format markdown
```

ADB snapshot path:

```bash
adb shell ip route
adb shell ip addr
adb shell dumpsys connectivity
```

Trigger template:

```bash
# 예시: Wi-Fi를 끄고 cellular로 넘기는 후보. 실제 device 정책 확인 필수.
ANDROID_NETWORK_CHANGE_CMD='adb shell svc wifi disable'
ANDROID_NETWORK_RESTORE_CMD='adb shell svc wifi enable'
```

Android trial wrapper는 before/after route/address/connectivity snapshot을 수집하고 `client-path-change-summary.json`으로 요약한다.

## 4. Controlled public active trial flow

baseline PASS 이후 active trial은 다음 순서로만 진행한다.

```bash
set -a
source harness/config/controlled-public-origin.env
set +a

python3 tools/check_controlled_public_config.py --require-active-ready
python3 tools/check_handover_readiness.py --format markdown
python3 tools/build_final_handover_trial_packet.py \
  --use-local-config \
  --output docs/results/final-handover-trial-packet-20260624.md
```

trial 실행 후:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py \
  --trial-id <trial-id> \
  --artifact-dir repro/quic-go-min-repro/artifacts/<trial-id> \
  --require-final-countable \
  --require-complete

python3 tools/validate_final_handover_trial_artifact.py \
  --trial-id <trial-id> \
  --artifact-dir repro/quic-go-min-repro/artifacts/<trial-id> \
  --require-final-countable
```

## 5. 판정 기준

| evidence | pass 기준 |
| --- | --- |
| client path summary | `client_active_path_changed` |
| server request log | expected workload requests complete |
| server qlog | PATH_CHALLENGE/PATH_RESPONSE and HTTP/3 frame evidence |
| Chrome NetLog | no clear replacement-session evidence for Chrome final success |
| application result | no manual refresh/retry required unless experiment condition is explicitly an app-retry variant |

논문에서 browser-level CM success로 쓸 수 있는 최소 classification은 `possible_connection_migration`이다. `multiple_quic_sessions_without_client_path_change`, `no_path_change_after_trigger`, `tuple_changed_without_path_validation`은 negative/control 결과로만 사용한다.
