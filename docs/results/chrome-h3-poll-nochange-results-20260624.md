# Chrome local HTTP/3 polling no-change baseline 결과

작성일: 2026-06-24  
목적: Chrome browser가 quic-go HTTP/3 test origin에서 일정 시간 동안 sequential fetch workload를 유지할 수 있는지 확인한다. 이 실험은 network-change를 넣기 전의 no-change baseline이다.

## 1. 실험 환경

| 항목 | 값 |
| --- | --- |
| Browser | Google Chrome 149.0.7827.158 |
| Mode | headless Chrome |
| Server | quic-go `cmd/h3server` |
| Origin | `https://127.0.0.1:4443` |
| Page | `GET /browser-poll?count=5&interval_ms=300&label=chrome-poll` |
| Poll requests | five sequential `GET /poll` fetch requests |
| TLS | local self-signed cert + Chrome SPKI exception |
| QUIC forcing | `--origin-to-force-quic-on=127.0.0.1:4443` |
| Network change | none |
| Artifact | `repro/quic-go-min-repro/artifacts/chrome-h3-poll-nochange-classifier-pass` |

## 2. 실행 명령

```bash
cd repro/quic-go-min-repro
WORKLOAD=poll POLL_COUNT=5 POLL_INTERVAL_MS=300 RUN_ID=chrome-h3-poll-nochange-classifier-pass ./scripts/run-chrome-h3-local.sh
```

## 3. 결과

요약:

```json
{
  "status": "PASS",
  "workload": "poll",
  "expected_requests": 6,
  "server_request_count": 6,
  "server_remote_addrs": ["127.0.0.1:60133"],
  "netlog_parser_mode": "json",
  "netlog_target_quic_session_count": 1,
  "netlog_target_using_quic_job_count": 6,
  "netlog_target_url_request_count": 6,
  "qlog_has_h3": true,
  "qlog_has_path_validation": false,
  "classification": "no_path_change_baseline"
}
```

server request sequence:

```text
GET /browser-poll  label=chrome-poll    remote=127.0.0.1:60133
GET /poll          label=chrome-poll-1  remote=127.0.0.1:60133
GET /poll          label=chrome-poll-2  remote=127.0.0.1:60133
GET /poll          label=chrome-poll-3  remote=127.0.0.1:60133
GET /poll          label=chrome-poll-4  remote=127.0.0.1:60133
GET /poll          label=chrome-poll-5  remote=127.0.0.1:60133
```

qlog summary:

| event | count |
| --- | ---: |
| `connection_started` | 1 |
| `connection_closed` | 1 |
| `packet_sent` | 22 |
| `packet_received` | 19 |
| `http3_frame` | 20 |
| `chosen_alpn` | 1 |
| `path_challenge` | 0 |
| `path_response` | 0 |

NetLog 핵심 evidence:

```text
target QUIC_SESSION count: 1
target HTTP_STREAM_JOB using_quic=true count: 6
target URL_REQUEST_START_JOB count: 6
target non-QUIC HTTP_STREAM_JOB count: 0
```

## 4. 해석

Chrome browser가 local quic-go H3 origin에서 일정 시간 동안 sequential fetch workload를 HTTP/3로 처리할 수 있음을 확인했다.

모든 server request의 `remote_addr`가 `127.0.0.1:60133`으로 같았고 qlog에 `PATH_CHALLENGE`/`PATH_RESPONSE`가 없었다. 따라서 classifier는 이 run을 `no_path_change_baseline`으로 분류했다.

NetLog에는 `QUIC_CONNECTION_MIGRATION_MODE` event가 관찰됐다. 그러나 이 event는 Chrome의 migration mode/configuration evidence로 해석해야 하며, 실제 migration 발생 evidence가 아니다. 실제 migration evidence로 쓰려면 tuple change, qlog path validation, 동일 target QUIC session 유지 여부가 함께 필요하다.

## 5. 다음 실험으로 이어지는 점

이 baseline은 다음 network-change 실험의 비교 기준이다.

다음 실험에서는 같은 `WORKLOAD=poll`을 유지하고 `NETWORK_CHANGE_CMD`를 넣어야 한다. 판정 기준은 다음과 같다.

| classification | 해석 |
| --- | --- |
| `possible_connection_migration` | remote tuple change + qlog path validation + target QUIC session 1개 |
| `reconnect_or_multiple_sessions` | remote tuple change가 있으나 target QUIC session이 여러 개 |
| `tuple_changed_without_path_validation` | server tuple은 바뀌었지만 qlog path validation이 없음 |
| `browser_h3_request_failed` | workload 자체가 완료되지 않음 |
| `no_path_change_baseline` | network change가 관찰되지 않음 |

현재 결론은 "Chrome network-change 실험을 걸 수 있는 long-lived browser workload와 classifier가 준비됐다"이다. 이 결과를 "Chrome Connection Migration이 된다"로 해석하면 안 된다.
