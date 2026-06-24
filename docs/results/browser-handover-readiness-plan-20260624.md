# Browser handover readiness and next experiment plan

작성일: 2026-06-24

## 1. 목적

Chrome public natural H3 baseline과 public Alt-Svc target survey 이후, 실제 browser/network-change 실험으로 넘어갈 수 있는지 현재 로컬 장비 상태와 필요한 실험 조건을 점검했다.

이 문서는 connection migration 결과 보고서가 아니라 다음 실험을 안전하게 설계하기 위한 readiness report다.

## 2. 현재 readiness 점검

확인 명령:

```bash
command -v adb
adb devices
networksetup -listallnetworkservices
ifconfig
command -v aws
aws sts get-caller-identity
```

관찰:

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| ADB | 설치됨 | Android/Cronet 실험 도구는 있음 |
| Android device | 연결된 device 없음 | Android Chrome/Cronet handover는 지금 즉시 실행 불가 |
| active local interface | `en0` Wi-Fi, `lo0`, `awdl0` | 실제 active path switch를 만들 보조 data interface가 확인되지 않음 |
| network services | `USB 10/100 LAN`, `Thunderbolt Bridge`, `Wi-Fi`, `iPhone USB` | `iPhone USB`는 후보지만 현재 active IP evidence는 없음 |
| AWS CLI | 설치됨 | controlled public origin 자동 구축 후보 |
| AWS identity | readiness check에서 caller identity 확인 안 됨 | public origin 자동 구축 전 credential/profile 확인 필요 |

## 3. 지금 실행하면 안 되는 것

현재 상태에서 바로 Wi-Fi를 끄는 실험은 피해야 한다.

이유:

1. active 대체 경로가 확인되지 않아 연결이 끊기기만 할 수 있다.
2. public third-party endpoint는 upload/download/dashboard workload를 제어할 수 없다.
3. migration success/failure를 해석하려면 server qlog와 server-side remote tuple evidence가 필요하다.
4. local origin은 natural Alt-Svc browser discovery control을 통과하지 못했다.

## 4. 다음 실험의 필요 조건

Chrome browser CM 실험을 하려면 다음 네 가지를 먼저 만족해야 한다.

| 조건 | 필요 이유 |
| --- | --- |
| controlled public WebPKI origin | Chrome이 forced QUIC 없이 natural H3를 선택해야 함 |
| server qlog / request log | migration인지 reconnect인지 구분해야 함 |
| long-running workload | network change 중에도 request가 살아 있어야 함 |
| active secondary network | source IP/interface 변화가 실제로 발생해야 함 |

## 5. 권장 실험 순서

### 5.1 Controlled public origin 구축

권장 구성:

```text
Chrome desktop or Android
  -> public DNS + trusted certificate
  -> EC2 direct-origin quic-go h3server
```

필요 항목:

- public DNS name
- trusted certificate, 예: ACM/Let's Encrypt/Caddy/Certbot 중 하나
- UDP 443 open
- TCP 443 bootstrap 또는 HTTPS/SVCB/Alt-Svc discovery path
- server-side qlog and request JSON

먼저 no-change natural H3 baseline을 통과시킨다.

### 5.2 Desktop Chrome active path-change 실험

전제:

- `en0` Wi-Fi 외에 `iPhone USB` 또는 Ethernet이 active IP를 가진 상태
- Chrome target origin이 natural H3로 확인된 상태

workload:

- slow subresource
- streaming download
- upload body
- dashboard polling

분류:

| classification | 조건 |
| --- | --- |
| `possible_connection_migration` | same QUIC session, server tuple change, qlog path validation |
| `browser_reconnect` | workload succeeds but new QUIC session observed |
| `application_retry` | JS/fetch retry로 복구 |
| `task_failure` | upload/download/dashboard task fails |
| `no_active_path_change` | interface toggle은 있었지만 server tuple 변화 없음 |

### 5.3 Android Chrome / Cronet 실험

전제:

- ADB device connected
- Wi-Fi and cellular both available
- Chrome NetLog or Cronet NetLog collection path confirmed

측정:

- task success
- stall time
- retry count
- server tuple change
- qlog path validation
- NetLog QUIC session continuity
- Android network callback timing

## 6. 논문상 의미

현재까지 결과는 다음처럼 정리된다.

> Browser layer 연구의 다음 병목은 QUIC 구현체 자체가 아니라 controlled public WebPKI origin과 실제 active network-change trigger다.

따라서 다음 장의 핵심 실험은 “Chrome/Cronet이 실제 Wi-Fi/LTE 또는 Wi-Fi/USB tethering 전환에서 migration을 선택하는가, 아니면 reconnect/retry로 처리하는가”가 되어야 한다.

## 7. 다음 액션

1. AWS profile/caller identity를 확인한다.
2. controlled public origin을 자동 구축하는 하네스를 만든다.
3. no-change natural H3 browser workload를 먼저 통과시킨다.
4. active secondary network가 준비된 상태에서만 handover trigger를 실행한다.
5. 결과는 migration, reconnect, retry, failure 네 가지로 분류한다.
