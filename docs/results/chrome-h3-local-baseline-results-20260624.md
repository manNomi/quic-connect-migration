# Chrome local HTTP/3 baseline 결과

작성일: 2026-06-24  
목적: Chrome browser가 quic-go HTTP/3 test origin으로 실제 HTTP/3 request를 보낼 수 있는지 확인한다. 이 실험은 Connection Migration 실험이 아니라 브라우저 baseline 실험이다.

## 1. 실험 환경

| 항목 | 값 |
| --- | --- |
| Browser | Google Chrome 149.0.7827.158 |
| Mode | headless Chrome |
| Server | quic-go `cmd/h3server` |
| Origin | `https://127.0.0.1:4443` |
| Request | `GET /download?bytes=128&label=chrome-baseline` |
| TLS | local self-signed cert + Chrome SPKI exception |
| QUIC forcing | `--origin-to-force-quic-on=127.0.0.1:4443` |
| Artifact | `repro/quic-go-min-repro/artifacts/chrome-h3-local-spki-pass` |

## 2. 실행 명령

```bash
cd repro/quic-go-min-repro
RUN_ID=chrome-h3-local-spki-pass ./scripts/run-chrome-h3-local.sh
```

## 3. 결과

요약:

```json
{
  "status": "PASS",
  "chrome_exit": 124,
  "chrome_completed_cleanly": false,
  "chrome_timed_out_after_request": true,
  "server_ok": true,
  "server_request_count": 1,
  "server_remote_addr": "127.0.0.1:65402",
  "netlog_has_quic_session": true,
  "qlog_has_h3": true,
  "qlog_has_path_validation": false
}
```

server result:

```json
{
  "ok": true,
  "requests": [
    {
      "label": "chrome-baseline",
      "method": "GET",
      "path": "/download",
      "remote_addr": "127.0.0.1:65402",
      "response_bytes": 128,
      "workload": "download",
      "decode_successful": true
    }
  ]
}
```

qlog summary:

| event | count |
| --- | ---: |
| `connection_started` | 1 |
| `connection_closed` | 1 |
| `packet_sent` | 13 |
| `packet_received` | 12 |
| `http3_frame` | 5 |
| `chosen_alpn` | 1 |
| `path_challenge` | 0 |
| `path_response` | 0 |

NetLog 핵심 event:

```text
QUIC_SESSION host=127.0.0.1 port=4443 versions=RFCv1
URL_REQUEST_START_JOB method=GET url=https://127.0.0.1:4443/download?bytes=128&label=chrome-baseline
HTTP_STREAM_JOB destination=https://127.0.0.1:4443 using_quic=true
```

## 4. 해석

Chrome browser가 local quic-go H3 origin에 대해 실제 QUIC/HTTP/3 request를 보낼 수 있음을 확인했다.

첫 시도에서는 Chrome이 QUIC session을 만들었지만 self-signed certificate를 신뢰하지 못해 `ERR_QUIC_PROTOCOL_ERROR`가 발생했다. NetLog의 close reason은 `CERTIFICATE_VERIFY_FAILED`였다.

두 번째 시도에서는 script가 local cert/key를 생성하고 SPKI hash를 Chrome에 전달했다. 이 조건에서 Chrome NetLog, server result, qlog가 모두 HTTP/3 request 도달을 지지했다.

## 5. 한계

이 실험은 browser baseline이다. 다음은 아직 검증하지 않았다.

- Chrome network change 시 기존 HTTP/3 connection migration 여부
- Chrome에서 source tuple 변경 후 같은 connection 유지 여부
- Android Chrome Wi-Fi/LTE handover
- Cronet `ConnectionMigrationOptions` enabled/disabled 비교
- AWS NLB public origin에서 Chrome browser migration 여부

따라서 이 결과를 "Chrome Connection Migration이 된다"로 해석하면 안 된다. 현재 결론은 "Chrome을 이용한 후속 CM 실험을 진행할 수 있는 H3 baseline이 확보됐다"이다.
