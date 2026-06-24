# Chrome Wi-Fi IP HTTP/3 limited control 결과

작성일: 2026-06-24
목적: Chrome browser HTTP/3 실험을 `127.0.0.1` loopback origin에서 벗어나, 같은 머신의 Wi-Fi IP origin으로 확장한다. 또한 non-loopback local origin에서 inactive network service toggle이 QUIC path migration evidence를 만드는지 확인한다.

## 1. 실험 환경

| 항목 | 값 |
| --- | --- |
| Browser | Google Chrome 149.0.7827.158 |
| Mode | headless Chrome |
| Server | quic-go `cmd/h3server` |
| Server listen | `0.0.0.0:4443` |
| Chrome origin | `https://192.168.32.190:4443` |
| Active interface | Wi-Fi `en0`, address `192.168.32.190` |
| Workload | `GET /browser-slow` + streaming `GET /slow-js` |
| TLS | local self-signed cert + Chrome SPKI exception |
| QUIC forcing | `--origin-to-force-quic-on=192.168.32.190:4443` |

주의: `192.168.32.190`은 실행 시점의 local Wi-Fi IP다. 재현 시에는 `ipconfig getifaddr en0`으로 현재 값을 확인해야 한다.

## 2. No-Change Baseline

실행:

```bash
cd repro/quic-go-min-repro
WIFI_IP="$(ipconfig getifaddr en0)"
WORKLOAD=slow \
LISTEN_ADDR=0.0.0.0:4443 \
ORIGIN_ADDR="${WIFI_IP}:4443" \
SLOW_DURATION_MS=6000 \
SLOW_CHUNKS=6 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=15 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
RUN_ID=chrome-h3-slow-wifi-ip-nochange \
./scripts/run-chrome-h3-local.sh
```

결과:

```json
{
  "status": "PASS",
  "classification": "no_path_change_baseline",
  "server_request_count": 2,
  "server_remote_addrs": ["192.168.32.190:61509"],
  "netlog_parser_mode": "json",
  "netlog_target_quic_session_count": 1,
  "netlog_target_using_quic_job_count": 2,
  "qlog_has_path_validation": false
}
```

해석:

Chrome browser가 local Wi-Fi IP origin으로 HTTP/3 slow workload를 완료했다. server가 본 remote tuple은 `192.168.32.190:61509` 하나였고 qlog path validation은 없었다. 따라서 이 run은 non-loopback local origin baseline이다.

## 3. Inactive Interface Toggle Control

실행:

```bash
cd repro/quic-go-min-repro
WIFI_IP="$(ipconfig getifaddr en0)"
WORKLOAD=slow \
LISTEN_ADDR=0.0.0.0:4443 \
ORIGIN_ADDR="${WIFI_IP}:4443" \
SLOW_DURATION_MS=8000 \
SLOW_CHUNKS=8 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=18 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
RUN_ID=chrome-h3-slow-wifi-ip-inactive-if-toggle \
./scripts/run-chrome-h3-local.sh
```

결과:

```json
{
  "status": "PASS",
  "classification": "no_path_change_baseline",
  "network_change_exit": 0,
  "server_request_count": 2,
  "server_remote_addrs": ["192.168.32.190:56596"],
  "netlog_parser_mode": "json",
  "netlog_target_quic_session_count": 1,
  "netlog_target_using_quic_job_count": 2,
  "qlog_has_path_validation": false
}
```

server request sequence:

```text
GET /browser-slow  label=chrome-slow  remote=192.168.32.190:56596
GET /slow-js       label=chrome-slow  remote=192.168.32.190:56596
```

qlog summary:

| event | count |
| --- | ---: |
| `connection_started` | 1 |
| `connection_closed` | 1 |
| `packet_sent` | 32 |
| `packet_received` | 29 |
| `http3_frame` | 16 |
| `chosen_alpn` | 1 |
| `path_challenge` | 0 |
| `path_response` | 0 |

NetLog 핵심 evidence:

```text
target QUIC_SESSION count: 1
target HTTP_STREAM_JOB using_quic=true count: 2
target non-QUIC HTTP_STREAM_JOB count: 0
QUIC_CONNECTION_MIGRATION_MODE count: 8
NETWORK_QUALITY_CHANGED count: 1
```

## 4. 해석

이번 실험은 loopback origin의 한계를 일부 줄였다. Chrome이 `192.168.32.190:4443`이라는 non-loopback local origin에 대해 HTTP/3 request를 만들었고, server도 remote tuple을 `192.168.32.190:<port>`로 관찰했다.

그러나 inactive `Thunderbolt Bridge` service toggle은 실제 active Wi-Fi path를 바꾸지 않았다. 그 결과 server remote tuple은 하나로 유지됐고 qlog에 `PATH_CHALLENGE`/`PATH_RESPONSE`가 없었다. classifier도 `no_path_change_baseline`을 반환했다.

따라서 이 결과는 "Chrome이 migration에 실패했다"가 아니라 다음처럼 해석해야 한다.

> non-loopback local origin에서도 inactive interface configuration change만으로는 QUIC Connection Migration을 유발하지 못한다. 실제 browser CM 검증에는 active path가 바뀌는 public/non-loopback origin, real Wi-Fi/LTE handover, 또는 통제된 active route change가 필요하다.

## 5. 논문상 의미

이 결과는 Chrome 브라우저 실험을 설계할 때 중요한 negative/control evidence다.

- HTTP/3 browser workload 자체는 Chrome에서 성립한다.
- local Wi-Fi IP origin도 forced QUIC 조건에서 동작한다.
- 하지만 "network setting을 바꿨다"는 사실만으로 migration 실험이라고 볼 수 없다.
- migration evidence는 tuple change와 qlog path validation, 그리고 Chrome NetLog session continuity를 함께 요구해야 한다.

현재 다음 연구 단계는 public/AWS origin 또는 Android/Cronet 기반 active interface handover다.
