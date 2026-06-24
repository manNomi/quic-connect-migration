# Android Chrome controlled public H3 network-change harness

작성일: 2026-06-24

## 1. 목적

Android Chrome에서 controlled public WebPKI origin의 long-running HTTP/3 workload를 열고, 실행 중 Wi-Fi/LTE 같은 active network change를 넣기 위한 ADB 기반 wrapper를 추가했다.

이 단계는 아직 Android handover 결과가 아니다. 현재 로컬 환경에는 ADB로 연결된 Android device가 없으므로, 이번 결과는 실행 가능한 실험 harness와 판정 기준을 준비한 것이다.

## 2. 추가한 파일

- `tools/run_android_chrome_navigation.py`
- `repro/quic-go-min-repro/scripts/run-android-chrome-controlled-public-network-change.sh`
- `tools/classify_controlled_public_h3_network_change.py`의 `--browser-kind android-chrome` mode

## 3. 실행 전제

필수 precondition:

```text
ADB device
  adb devices 에 device 상태로 1대 이상 연결

controlled public origin
  DNS/WebPKI/TCP 443/UDP 443/Alt-Svc 준비

baseline summary
  status starts with PASS

Android active network-change command
  예: adb shell svc wifi disable / enable, 또는 테스트 기기별 셀룰러 전환 절차
```

Android Chrome은 현재 harness에서 Chrome desktop NetLog처럼 브라우저 내부 QUIC session artifact를 자동 수집하지 않는다. 따라서 판정은 server request log, server qlog, Android raw network snapshot, optional packet capture 중심으로 한다.

## 4. 실행 예시

Server side:

```bash
cd repro/quic-go-min-repro
RUN_ID=android-chrome-controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/android-chrome-controlled-public-h3-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
PUBLIC_ORIGIN_PORT=443 \
EXPECTED_REQUESTS=2 \
./scripts/run-controlled-public-h3-server.sh
```

Android side:

```bash
cd repro/quic-go-min-repro
RUN_ID=android-chrome-controlled-public-h3-network-change-001 \
ARTIFACT_DIR=artifacts/android-chrome-controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/android-chrome-controlled-public-h3-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-h3-application-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=15000&chunks=15&label=android-handover-slow' \
ANDROID_NETWORK_CHANGE_CMD='adb shell svc wifi disable' \
NETWORK_CHANGE_AFTER_SECONDS=3 \
ANDROID_CHROME_WAIT_SECONDS=18 \
./scripts/run-android-chrome-controlled-public-network-change.sh
```

다중 기기 환경에서는 `ANDROID_SERIAL=<adb serial>`을 지정한다. 공개 결과에는 raw serial을 남기지 않는다.

## 5. 결과 파일

```text
results/public-origin-readiness.json
results/android-chrome-navigation.json
results/network-change.json
results/android-chrome-controlled-public-h3-network-change-summary.json
android/connectivity-before.txt
android/connectivity-command-before.txt
android/connectivity-command-after.txt
android/connectivity-final.txt
android/ip-route-*.txt
android/ip-addr-*.txt
logs/network-change.log
```

`android/*.txt` 파일은 ignored raw artifact로 취급한다. 논문/공개 repo에는 요약과 판정 결과만 올린다.

## 6. 판정 기준

Android Chrome network-change summary에서 사용하는 핵심 classification:

| classification | status | 의미 |
| --- | --- | --- |
| `possible_connection_migration_server_qlog_only` | `PASS_FEASIBILITY` | server remote tuple change와 qlog path validation은 있지만 browser-internal QUIC session evidence가 없음 |
| `tuple_changed_without_path_validation` | `PASS_NEGATIVE_CONTROL` | network change 후 tuple은 바뀌었지만 QUIC path validation evidence 없음 |
| `no_path_change_after_trigger` | `PASS_NEGATIVE_CONTROL` | trigger 이후 server tuple 변화 없음 |
| `controlled_public_network_change_workload_failed` | `FAIL` | Android Chrome navigation 후 expected request count 미달 |

## 7. 논문상 의미

Android Chrome/Cronet 계열은 실제 모바일 handover 연구의 핵심 대상이다. 다만 이 harness만으로는 Chrome desktop NetLog와 같은 browser-internal session evidence를 제공하지 않으므로, 성공 claim은 다음처럼 제한해야 한다.

```text
browser = Android Chrome
evidence = server request log + server qlog + Android network snapshot + optional packet capture
claim strength = feasibility unless stronger client-side QUIC logs are added
```

논문 본 실험으로 채택하려면 적어도 다음이 필요하다.

1. ADB device 연결
2. controlled public application H3 baseline PASS
3. 실제 Wi-Fi/LTE 또는 active default network change command
4. server qlog의 PATH_CHALLENGE/PATH_RESPONSE
5. workload success/failure와 재시도 여부 기록
