# Chrome local HTTP/3 sequence baseline 결과

작성일: 2026-06-24  
목적: Chrome browser가 quic-go HTTP/3 test origin에서 HTML page와 하위 resource를 연속으로 가져올 수 있는지 확인한다. 이 실험은 Connection Migration 실험이 아니라 브라우저 HTTP/3 sequence baseline이다.

## 1. 실험 환경

| 항목 | 값 |
| --- | --- |
| Browser | Google Chrome 149.0.7827.158 |
| Mode | headless Chrome |
| Server | quic-go `cmd/h3server` |
| Origin | `https://127.0.0.1:4443` |
| Request | `GET /browser-sequence?resources=2&bytes=128&label=chrome-sequence` |
| Subresources | two `GET /pixel` SVG image resources |
| TLS | local self-signed cert + Chrome SPKI exception |
| QUIC forcing | `--origin-to-force-quic-on=127.0.0.1:4443` |
| Artifact | `repro/quic-go-min-repro/artifacts/chrome-h3-sequence-vtime-pass` |

## 2. 실행 명령

```bash
cd repro/quic-go-min-repro
WORKLOAD=sequence RUN_ID=chrome-h3-sequence-vtime-pass ./scripts/run-chrome-h3-local.sh
```

## 3. 결과

요약:

```json
{
  "status": "PASS",
  "workload": "sequence",
  "expected_requests": 3,
  "chrome_exit": 124,
  "chrome_timed_out_after_request": true,
  "server_ok": true,
  "server_request_count": 3,
  "server_remote_addrs": ["127.0.0.1:53299"],
  "server_request_labels": [
    "chrome-sequence",
    "chrome-sequence-1",
    "chrome-sequence-2"
  ],
  "netlog_target_quic_session_count": 1,
  "netlog_target_using_quic_job_count": 3,
  "netlog_target_url_request_count": 3,
  "qlog_has_h3": true,
  "qlog_has_path_validation": false
}
```

server result 핵심:

```text
GET /browser-sequence  label=chrome-sequence    remote=127.0.0.1:53299
GET /pixel             label=chrome-sequence-1  remote=127.0.0.1:53299
GET /pixel             label=chrome-sequence-2  remote=127.0.0.1:53299
```

qlog summary:

| event | count |
| --- | ---: |
| `connection_started` | 1 |
| `connection_closed` | 1 |
| `packet_sent` | 18 |
| `packet_received` | 17 |
| `http3_frame` | 11 |
| `chosen_alpn` | 1 |
| `path_challenge` | 0 |
| `path_response` | 0 |

NetLog 핵심 evidence:

```text
target QUIC_SESSION count: 1
target HTTP_STREAM_JOB using_quic=true count: 3
target URL_REQUEST_START_JOB count: 3
```

## 4. 해석

Chrome browser가 local quic-go H3 origin에서 page request와 하위 resource request를 HTTP/3로 처리할 수 있음을 확인했다.

모든 server request의 `remote_addr`가 `127.0.0.1:53299`로 같았고, NetLog에서도 target origin에 대해 하나의 QUIC session과 세 개의 `using_quic=true` stream job이 관찰됐다. 따라서 후속 network-change 실험에서 비교할 수 있는 브라우저 workload baseline이 생겼다.

## 5. 한계

이 실험은 network path를 바꾸지 않는다. 따라서 다음은 아직 검증하지 않았다.

- Chrome network change 시 기존 HTTP/3 session migration 여부
- server qlog의 `PATH_CHALLENGE`/`PATH_RESPONSE` 발생 여부
- Android Chrome Wi-Fi/LTE handover
- mid-flight upload/download 중 browser task survival
- Service Worker나 application-level retry와의 상호작용

현재 결론은 "Chrome을 이용한 page+subresource HTTP/3 baseline이 확보됐다"이다. 이 결과를 "Chrome Connection Migration이 된다"로 해석하면 안 된다.
