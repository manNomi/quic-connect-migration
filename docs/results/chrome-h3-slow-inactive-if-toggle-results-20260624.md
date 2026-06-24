# Chrome slow HTTP/3 inactive interface toggle 결과

작성일: 2026-06-24
목적: Chrome browser가 느리게 전송되는 HTTP/3 subresource를 받는 중, macOS inactive network service toggle이 QUIC path migration evidence를 만드는지 확인한다. 이 실험은 실제 Wi-Fi/LTE handover가 아니라 limited negative/control 실험이다.

## 1. 실험 환경

| 항목 | 값 |
| --- | --- |
| Browser | Google Chrome 149.0.7827.158 |
| Mode | headless Chrome |
| Server | quic-go `cmd/h3server` |
| Origin | `https://127.0.0.1:4443` |
| Page | `GET /browser-slow?duration_ms=8000&chunks=8&label=chrome-slow` |
| Slow subresource | streaming `GET /slow-js`, 8 chunks, 1000ms delay |
| Network trigger | `Thunderbolt Bridge` network service off/on |
| Active network | Wi-Fi `en0`; not modified |
| TLS | local self-signed cert + Chrome SPKI exception |
| QUIC forcing | `--origin-to-force-quic-on=127.0.0.1:4443` |
| Artifact | `repro/quic-go-min-repro/artifacts/chrome-h3-slow-inactive-if-toggle` |

## 2. 실행 명령

```bash
cd repro/quic-go-min-repro
WORKLOAD=slow \
SLOW_DURATION_MS=8000 \
SLOW_CHUNKS=8 \
CHROME_VIRTUAL_TIME_BUDGET_MS=0 \
CHROME_TIMEOUT_SECONDS=18 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=2 \
NETWORK_CHANGE_CMD='networksetup -setnetworkserviceenabled "Thunderbolt Bridge" off; sleep 1; networksetup -setnetworkserviceenabled "Thunderbolt Bridge" on' \
RUN_ID=chrome-h3-slow-inactive-if-toggle \
./scripts/run-chrome-h3-local.sh
```

## 3. 결과

요약:

```json
{
  "status": "PASS",
  "workload": "slow",
  "expected_requests": 2,
  "server_request_count": 2,
  "server_remote_addrs": ["127.0.0.1:53206"],
  "network_change_exit": 0,
  "netlog_parser_mode": "json",
  "netlog_target_quic_session_count": 1,
  "netlog_target_using_quic_job_count": 2,
  "qlog_has_h3": true,
  "qlog_has_path_validation": false,
  "classification": "no_path_change_baseline"
}
```

server request sequence:

```text
GET /browser-slow  label=chrome-slow  remote=127.0.0.1:53206
GET /slow-js       label=chrome-slow  remote=127.0.0.1:53206
```

qlog summary:

| event | count |
| --- | ---: |
| `connection_started` | 1 |
| `connection_closed` | 1 |
| `packet_sent` | 26 |
| `packet_received` | 22 |
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

Chrome browser는 slow HTTP/3 subresource를 받는 동안 workload를 완료했다. network-change hook도 `exit=0`으로 실행됐고 `Thunderbolt Bridge` service는 실험 후 Enabled 상태로 복구됐다.

그러나 server가 본 remote tuple은 `127.0.0.1:53206` 하나뿐이었고, qlog에 `PATH_CHALLENGE`/`PATH_RESPONSE`가 없었다. 따라서 classifier는 이 run을 `no_path_change_baseline`으로 분류했다.

이 결과는 "Chrome이 migration에 실패했다"가 아니라, 더 좁게 "inactive interface service toggle은 local loopback H3 connection에서 실제 path migration을 만들지 못했다"로 해석해야 한다.

## 5. 한계

- active Wi-Fi `en0`는 건드리지 않았다.
- origin이 `127.0.0.1` loopback이므로 실제 외부 network path가 바뀌지 않는다.
- Wi-Fi/LTE handover, active route change, non-loopback public origin을 검증한 것이 아니다.
- `QUIC_CONNECTION_MIGRATION_MODE` NetLog event는 migration mode/configuration evidence이지 실제 migration 발생 evidence가 아니다.

현재 결론은 "Chrome browser network-change 실험에는 실제 active path가 바뀌는 trigger와 non-loopback origin이 필요하다"이다.
