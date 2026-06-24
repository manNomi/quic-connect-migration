# AWS NLB HTTP/3 Workload Results

작성일: 2026-06-24  
최종 상태: PASS  
주요 artifact: `harness/results/aws-nlb-h3-tcp-quic-443-20260623T165841Z/`

## 1. Research Question

질문:

> AWS NLB `TCP_QUIC :443`에서 QUIC-LB plaintext CID 기반 active migration이 성공할 때, 같은 HTTP/3 connection 위의 upload/download request도 manual retry 없이 완료되는가?

결론:

> PASS. NLB `TCP_QUIC :443` 경로에서 HTTP/3 POST `/upload` before request를 완료한 뒤 active migration을 수행했고, 같은 HTTP/3 connection에서 GET `/download` after request도 성공했다.

## 2. Setup

| 항목 | 값 |
| --- | --- |
| run id | `aws-nlb-h3-tcp-quic-443-20260623T165841Z` |
| AWS region | `ap-northeast-2` |
| NLB protocol | `TCP_QUIC` |
| listener port | `443` |
| workload | `h3` |
| client | local `quic-go` `cmd/h3client` |
| server | EC2 `quic-go` `cmd/h3server` |
| target count | 2 |
| successful target | `target-a` |
| CID format | `0x00 + 8-byte Server ID + 7-byte nonce` |
| before task | POST `/upload`, 64 KiB |
| after task | GET `/download`, 64 KiB |
| cleanup | listener, NLB, target group, EC2 instances, security group, AWS key pair deleted |

## 3. PASS Evidence

Summary:

```json
{
  "status": "PASS",
  "workload": "h3",
  "client_ok": true,
  "client_socket_a": "[::]:54110",
  "client_socket_b": "[::]:50930",
  "client_local_addr_changed_to_socket_b": true,
  "server_success_count": 1,
  "successful_target": "target-a"
}
```

Client result:

```json
{
  "ok": true,
  "server_addr": "qcm-nlb-20260623165841-1245739fc4676f97.elb.ap-northeast-2.amazonaws.com:443",
  "socket_a_local_addr": "[::]:54110",
  "socket_b_local_addr": "[::]:50930",
  "connection_local_addr_after_after_request": "[::]:50930",
  "probe_duration_millis": 9,
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
  "listen_addr": "0.0.0.0:443",
  "connection_id_mode": "aws-quic-lb-plaintext",
  "aws_server_id": "a1b2c3d4e5f65890",
  "requests": [
    {
      "label": "before",
      "method": "POST",
      "path": "/upload",
      "remote_addr": "211.60.158.133:54110",
      "request_bytes": 65536
    },
    {
      "label": "after",
      "method": "GET",
      "path": "/download",
      "remote_addr": "211.60.158.133:50930",
      "response_bytes": 65536
    }
  ]
}
```

Interpretation:

- Initial HTTP/3 POST upload reached `target-a`.
- Client source port changed from `54110` to `50930`.
- Same `target-a` received the after HTTP/3 GET download request.
- Client completed both HTTP/3 tasks without manual retry.
- Server observed request remote address change from `211.60.158.133:54110` to `211.60.158.133:50930`.

## 4. qlog Evidence

HTTP/3 evidence:

```text
chosen_alpn=h3
POST /upload HEADERS and DATA frames observed
GET /download?bytes=65536&label=after HEADERS observed after migration
after download DATA frame observed
```

Path validation:

```text
client path_challenge data=f04c5a4ec246cde2
server path_response data=f04c5a4ec246cde2
server path_challenge data=788024fd19e2a11b
client path_response data=788024fd19e2a11b
```

## 5. Cleanup Verification

별도 AWS residue check 결과:

```text
instances=0
security_groups=0
key_pairs=0
nlbs_named_qcm=0
target_groups_named_qcm_q=0
local_ssh_key_files=0
```

## 6. Paper Use

This result upgrades the application/deployment bridge claim:

> AWS NLB `TCP_QUIC :443` can preserve same-target HTTP/3 request continuity across active client source-port migration, when backend-generated CIDs match the NLB QUIC-LB plaintext Server ID format.

Limit:

> This is post-migration request continuity. It does not yet prove mid-flight upload or mid-flight download survival.

## 7. Next Step

The next experiment should trigger migration during the body transfer itself:

1. mid-flight upload: start POST body, migrate while body is still streaming, verify server receives the full body once.
2. mid-flight download: start GET response body, migrate while response is still streaming, verify client receives the full body once.
3. compare with HAProxy and CloudFront controls.
