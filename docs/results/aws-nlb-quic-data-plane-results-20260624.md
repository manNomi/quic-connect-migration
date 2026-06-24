# AWS NLB QUIC Data-Plane Results

작성일: 2026-06-24  
최종 상태: PASS  
주요 artifact: `harness/results/aws-nlb-quic-dp-20260623T160418Z/`

## 1. Research Question

질문:

> AWS Network Load Balancer의 QUIC passthrough가 QUIC-LB 형식의 server-routable Connection ID를 사용해, client UDP tuple 변경 후에도 같은 backend target으로 packet을 라우팅하는가?

결론:

> PASS. `quic-go` custom client/server와 AWS NLB `QUIC` listener/target group 구성에서 active path migration이 성공했고, 같은 target B가 migration 전후의 `before`/`after` stream payload를 모두 수신했다.

## 2. Setup

| 항목 | 값 |
| --- | --- |
| run id | `aws-nlb-quic-dp-20260623T160418Z` |
| AWS region | `ap-northeast-2` |
| NLB protocol | `QUIC` |
| listener port | `4242` |
| target group protocol | `QUIC` |
| target type | `instance` |
| target count | 2 |
| client | local `quic-go` custom client |
| server | EC2 `quic-go` custom server |
| payload | `before` 64 KiB + `after` 64 KiB |
| migration trigger | `AddPath -> Probe -> Switch` with a second UDP socket |
| cleanup | listener, NLB, target group, EC2 instances, security group, AWS key pair deleted |

Target server IDs:

| Target | Server ID |
| --- | --- |
| target-a | `0xa1b2c3d4e5f65890` |
| target-b | `0xa1b2c3d4e5f65999` |

## 3. Key Implementation Fix

첫 AWS data-plane 시도에서 중요한 실험 교훈이 있었다.

초기 구현은 CID를 다음처럼 만들었다.

```text
8-byte Server ID + 8-byte nonce
```

이 형식에서는 handshake와 일부 1-RTT 제어 패킷은 보였지만, payload `STREAM` frame이 target까지 안정적으로 도달하지 않았다.

AWS Load Balancer Controller의 Envoy QUIC 예제는 QUIC-LB `unencrypted_mode`와 `nonce_length_bytes: 7`을 사용한다. 이에 맞춰 CID를 다음 구조로 수정했다.

```text
1-byte config rotation byte(0x00) + 8-byte Server ID + 7-byte nonce
```

수정 후 `quic-go` server의 connection ID mode는 다음으로 기록된다.

```text
aws-quic-lb-plaintext
```

근거 링크:

- AWS NLB QUIC 소개: https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/
- AWS target registration requirements: https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-register-targets.html
- AWS Load Balancer Controller QUIC example: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/use_cases/quic/

## 4. Final PASS Evidence

Client result:

```json
{
  "ok": true,
  "socket_a_local_addr": "[::]:55957",
  "socket_b_local_addr": "[::]:59355",
  "connection_local_addr_after_dial": "[::]:55957",
  "connection_local_addr_after_after_payload": "[::]:59355",
  "switch_before_probe_error": "path not yet validated",
  "switch_before_probe_matched": true,
  "probe_duration_millis": 14,
  "local_addr_changed_to_socket_b": true
}
```

Server result:

```json
{
  "ok": true,
  "connection_id_mode": "aws-quic-lb-plaintext",
  "aws_server_id": "a1b2c3d4e5f65999",
  "received": [
    {
      "label": "before",
      "payload_bytes": 65536,
      "connection_remote_addr_at_receive": "211.60.158.133:55957"
    },
    {
      "label": "after",
      "payload_bytes": 65536,
      "connection_remote_addr_at_receive": "211.60.158.133:59355"
    }
  ]
}
```

Interpretation:

- Initial connection reached target-b.
- Client source port changed from `55957` to `59355`.
- The same target-b received both application payloads.
- The client did not reconnect or retry manually.
- qlog contains `PATH_CHALLENGE` and `PATH_RESPONSE` frames on both sides.

## 5. qlog Evidence

Path validation sequence:

| Side | Evidence |
| --- | --- |
| client | sent `path_challenge`, received `path_response`, sent reciprocal `path_response` |
| server | received `path_challenge`, sent `path_response` and `path_challenge`, received reciprocal `path_response` |

qlog frame counts from the PASS run:

| Side | STREAM frames | PATH_CHALLENGE | PATH_RESPONSE |
| --- | ---: | ---: | ---: |
| client qlog | 116 sent/observed events | 2 | 2 |
| server qlog | 109 received/observed events | 2 | 2 |

The server qlog confirms payload STREAM frames reached target-b after the CID format was corrected.

## 6. Classified Pre-Runs

| Run | Status | Classification | Lesson |
| --- | --- | --- | --- |
| `aws-nlb-quic-dp-20260623T153944Z` | FAIL_CLASSIFIED | harness timing | QUIC server timeout was too short and expired before NLB became available. |
| `aws-nlb-quic-dp-20260623T154734Z` | FAIL_CLASSIFIED | harness environment | EC2 non-login `nohup` shell could not find `go`; added `/usr/local/go/bin` fallback and startup check. |
| `aws-nlb-quic-dp-20260623T155524Z` | FAIL_CLASSIFIED | CID format | `8-byte Server ID + 8-byte nonce` was not the AWS QUIC-LB plaintext format. |
| `aws-nlb-quic-dp-20260623T160418Z` | PASS | positive data-plane | QUIC-LB plaintext CID format passed NLB routing and active migration. |

## 7. Paper Use

This result supports a stronger deployment-maturity claim:

> Connection Migration can survive an AWS managed load-balancing hop when the backend implementation generates NLB-routable QUIC-LB plaintext Connection IDs and the client validates/switches to a new path.

This should not be generalized to every HTTP/3 deployment. The result depends on:

- Server-generated CID format matching AWS NLB expectations.
- QUIC-aware load balancing rather than generic UDP or HTTP/3 proxying.
- Target registration with unique 8-byte `QuicServerId`.
- Application/server stack exposing enough CID control.

Recommended paper framing:

> AWS NLB QUIC provides a deployable positive control for CID-aware Connection Migration, while HAProxy provides a negative control showing that HTTP/3 support alone is insufficient.

## 8. Next Step

Recommended next experiments:

1. Add a negative AWS NLB control with intentionally wrong/default CID and collect NLB metric evidence if available.
2. Repeat the PASS with `TCP_QUIC` on port `443` to align with realistic HTTP/3 deployment.
3. Move from custom QUIC stream workload to HTTP/3 request/upload workload.
4. Later, compare custom client behavior with Cronet/Android client policy.
