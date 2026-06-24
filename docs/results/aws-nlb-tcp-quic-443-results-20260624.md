# AWS NLB TCP_QUIC :443 Results

작성일: 2026-06-24  
최종 상태: PASS  
주요 artifact: `harness/results/aws-nlb-tcp-quic-443-20260623T164138Z/`

## 1. Research Question

질문:

> AWS NLB `TCP_QUIC` listener/target group과 port `443` 구성에서도 QUIC-LB plaintext CID 기반 active Connection Migration이 같은 target으로 유지되는가?

결론:

> PASS. `TCP_QUIC :443` 구성에서도 client source port 변경 후 같은 target-b가 `before`/`after` 64 KiB stream payload를 모두 수신했다.

## 2. Setup

| 항목 | 값 |
| --- | --- |
| run id | `aws-nlb-tcp-quic-443-20260623T164138Z` |
| AWS region | `ap-northeast-2` |
| NLB protocol | `TCP_QUIC` |
| listener port | `443` |
| target group protocol | `TCP_QUIC` |
| target type | `instance` |
| target count | 2 |
| client | local `quic-go` custom client |
| server | EC2 `quic-go` custom server |
| CID format | `0x00 + 8-byte Server ID + 7-byte nonce` |
| payload | `before` 64 KiB + `after` 64 KiB |
| migration trigger | `AddPath -> Probe -> Switch` with a second UDP socket |
| cleanup | listener, NLB, target group, EC2 instances, security group, AWS key pair deleted |

Port 443 note:

> The EC2 target bootstrap set `net.ipv4.ip_unprivileged_port_start=0` so the non-root QUIC server and TCP health sidecar could bind to port `443` on temporary test instances.

## 3. PASS Evidence

Client result:

```json
{
  "ok": true,
  "server_addr": "qcm-nlb-20260623164138-303317bd11abf7ed.elb.ap-northeast-2.amazonaws.com:443",
  "socket_a_local_addr": "[::]:57897",
  "socket_b_local_addr": "[::]:56632",
  "connection_local_addr_after_after_payload": "[::]:56632",
  "switch_before_probe_error": "path not yet validated",
  "switch_before_probe_matched": true,
  "probe_duration_millis": 10,
  "local_addr_changed_to_socket_b": true
}
```

Server result:

```json
{
  "ok": true,
  "listen_addr": "0.0.0.0:443",
  "connection_id_mode": "aws-quic-lb-plaintext",
  "aws_server_id": "a1b2c3d4e5f65999",
  "received": [
    {
      "label": "before",
      "payload_bytes": 65536,
      "connection_remote_addr_at_receive": "211.60.158.133:57897"
    },
    {
      "label": "after",
      "payload_bytes": 65536,
      "connection_remote_addr_at_receive": "211.60.158.133:56632"
    }
  ]
}
```

Interpretation:

- Initial connection reached target-b.
- Client source port changed from `57897` to `56632`.
- Same target-b received both pre- and post-migration payloads.
- Client completed without manual retry.
- qlog contains `PATH_CHALLENGE` and `PATH_RESPONSE` frames on both sides.

## 4. qlog Evidence

Path validation sequence:

| Side | Evidence |
| --- | --- |
| client | sent `path_challenge`, received `path_response`, sent reciprocal `path_response` |
| server | received `path_challenge`, sent `path_response` and reciprocal `path_challenge`, received reciprocal `path_response` |

Representative qlog events:

```text
client path_challenge data=6b4264a9d1ef7f41
server path_response data=6b4264a9d1ef7f41
server path_challenge data=5f6a0144b4296421
client path_response data=5f6a0144b4296421
```

## 5. Paper Use

This result strengthens the deployment-control claim:

> AWS NLB QUIC Connection Migration is not only possible on a custom high port with `QUIC`; it also works on the more deployment-like `TCP_QUIC :443` configuration when the backend emits NLB-routable QUIC-LB plaintext CIDs.

Combined interpretation:

| Experiment | Result | Meaning |
| --- | --- | --- |
| `QUIC :4242` positive | PASS | baseline NLB QUIC passthrough can preserve migration |
| malformed/mismatched CID negative | PASS_NEGATIVE_CONTROL | CID layout/Server ID mapping is required |
| `TCP_QUIC :443` repeat | PASS | the positive claim generalizes to a more realistic listener/port mode |

## 6. Next Step

Recommended next experiments:

1. Add an HTTP/3 request/upload workload on top of the successful NLB transport path.
2. Run CloudFront viewer-edge limited control.
3. Compare custom-client transport continuity with Cronet/Android client policy.
