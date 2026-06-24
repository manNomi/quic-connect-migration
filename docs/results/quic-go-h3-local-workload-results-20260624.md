# quic-go Local HTTP/3 Workload Migration Results

작성일: 2026-06-24  
최종 상태: PASS  
주요 artifact: `experiments/quic-go-min-repro/artifacts/local-h3-workload-check/`

## 1. Research Question

질문:

> 직접 제어 가능한 quic-go `*quic.Conn` 위에 HTTP/3 client/server를 올린 뒤 active Connection Migration을 수행해도, 같은 HTTP/3 connection에서 migration 전후 request가 성공하는가?

결론:

> PASS. HTTP/3 POST `/upload` before request가 성공한 뒤 `AddPath -> Probe -> Switch`로 client source port를 변경했고, 같은 HTTP/3 connection에서 GET `/download` after request도 성공했다.

## 2. Scope

이 결과는 Phase 1 gate다.

- 검증함: migration 이후 같은 HTTP/3 connection에서 다음 request가 성공하는지
- 아직 검증하지 않음: upload body 전송 중 migration, download body 수신 중 migration

따라서 논문에는 “post-migration HTTP/3 request continuity”로 사용하고, “mid-flight web task survival”은 후속 실험으로 분리한다.

## 3. Setup

| 항목 | 값 |
| --- | --- |
| run id | `local-h3-workload-check` |
| client | `cmd/h3client` |
| server | `cmd/h3server` |
| protocol | HTTP/3 over QUIC |
| ALPN | `h3` |
| before task | POST `/upload`, 64 KiB deterministic payload |
| migration trigger | `AddPath -> Probe -> Switch` with a second UDP socket |
| after task | GET `/download?bytes=65536&label=after`, 64 KiB deterministic payload |

## 4. PASS Evidence

Client result:

```json
{
  "ok": true,
  "socket_a_local_addr": "[::]:63819",
  "socket_b_local_addr": "[::]:63361",
  "connection_local_addr_after_after_request": "[::]:63361",
  "local_addr_changed_to_socket_b": true,
  "tasks": [
    {"label": "before", "method": "POST", "path": "/upload", "status_code": 200},
    {"label": "after", "method": "GET", "path": "/download", "status_code": 200}
  ]
}
```

Server result:

```json
{
  "ok": true,
  "requests": [
    {
      "label": "before",
      "method": "POST",
      "path": "/upload",
      "remote_addr": "127.0.0.1:63819",
      "request_bytes": 65536
    },
    {
      "label": "after",
      "method": "GET",
      "path": "/download",
      "remote_addr": "127.0.0.1:63361",
      "response_bytes": 65536
    }
  ]
}
```

Interpretation:

- HTTP/3 before upload completed on source port `63819`.
- Path validation completed with PATH_CHALLENGE/PATH_RESPONSE.
- HTTP/3 after download completed on source port `63361`.
- Server observed the request-level remote address change from `127.0.0.1:63819` to `127.0.0.1:63361`.

## 5. qlog Evidence

Path validation:

```text
client path_challenge data=aaff6a76c2c4a4d5
server path_response data=aaff6a76c2c4a4d5
server path_challenge data=4635f0e075168f16
client path_response data=4635f0e075168f16
```

HTTP/3 evidence:

```text
chosen_alpn=h3
POST /upload headers and DATA frames observed
GET /download?bytes=65536&label=after headers observed
after download DATA frame payload_length=65697 observed
```

## 6. Implementation Added

New local gate:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
./scripts/run-local-h3-workload.sh
```

Added files:

- `experiments/quic-go-min-repro/cmd/h3client/main.go`
- `experiments/quic-go-min-repro/cmd/h3server/main.go`
- `experiments/quic-go-min-repro/scripts/run-local-h3-workload.sh`
- `experiments/aws-nlb-http3-workload-plan.md`

## 7. Next Step

Use this local gate to create an AWS NLB `TCP_QUIC :443` HTTP/3 workload variant. The AWS variant should reuse the successful CID format:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

After AWS post-migration request continuity passes, extend the workload to mid-flight upload and mid-flight download.
